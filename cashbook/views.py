

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CashTransaction,Account
from .forms import CashTransactionForm
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.http import JsonResponse
from products.models import Product

@login_required
def transaction_list(request):
    transactions = CashTransaction.objects.all()

    # Filter by account
    account_filter = request.GET.get("account")
    if account_filter:
        transactions = transactions.filter(account__code=account_filter)

    # Filter by reference user
    ref_filter = request.GET.get("reference")
    if ref_filter == "direct":
        transactions = transactions.filter(reference_user__isnull=True)
    elif ref_filter:
        transactions = transactions.filter(reference_user_id=ref_filter)

    return render(request, "cashbook/transaction_list.html", {
        "transactions": transactions,
        "accounts": Account.objects.all(),
        "users": User.objects.all(),
        "selected_account": account_filter,
        "selected_reference": ref_filter,
    })
        
    # if request.user.is_superuser or request.user.groups.filter(name__in=['Admin','Manager']).exists():
    #     transactions = CashTransaction.objects.all()
    # else:
    #     transactions = CashTransaction.objects.filter(user=request.user)
    # return render(request, "cashbook/transaction_list.html", {"transactions": transactions})


@login_required
def transaction_create(request):

    customer_id = request.GET.get("customer_id")  # 👈 check if coming from customer detail
    initial_data = {}
    if customer_id:
        initial_data["customer"] = customer_id

    if request.method == "POST":
        form = CashTransactionForm(request.POST)
        if form.is_valid():
            trans = form.save(commit=False)
            trans.user = request.user


            # calculate balances
            last_txn = CashTransaction.objects.order_by('date').last()
            opening = last_txn.closing_balance if last_txn else 0
            trans.opening_balance = opening
            trans.closing_balance = opening + trans.amount if trans.transaction_type == "INCOME" else opening - trans.amount
            
            # default to Direct if no reference chosen
            if not trans.reference_user:
                trans.reference_user = None  # None means "Direct shop work"

             # 👇 Auto-set amount from product if not entered manually
            if trans.product and (not trans.amount or trans.amount == 0):
                trans.amount = trans.product.sale_price

            trans.save()

            # # ✅ Redirect back to customer page if linked
            # if trans.customer:
            #     return redirect("customers:customer_detail", pk=trans.customer.id)
            # ✅ Smart redirect logic
            # ✅ Smart redirect
            if customer_id:  # means transaction was started from a customer page
                return redirect("customers:customer_detail", pk=trans.customer.id)
            else:  # normal cashbook entry
                return redirect("cashbook:transaction_list")

            # messages.success(request, "Transaction added successfully!")
            # return redirect("cashbook:transaction_list")
    else:
        form = CashTransactionForm(initial=initial_data)
    return render(request, "cashbook/transaction_form.html", {"form": form})


@login_required
def cashbook_summary(request):
    today = timezone.localdate()
    start_week = today - timedelta(days=today.weekday())


    # 📌 Handle date range filter (from-to)
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    # If no filter → use all
    txns = CashTransaction.objects.all()

    if from_date and to_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
            to_dt = datetime.strptime(to_date, "%Y-%m-%d").date()
            txns = CashTransaction.objects.filter(date__date__gte=from_dt, date__date__lte=to_dt)
        except ValueError:
            pass
    
    summary = {
        "today_income": CashTransaction.objects.filter(transaction_type="INCOME", date__date=today).aggregate(Sum("amount"))["amount__sum"] or 0,
        "today_expense": CashTransaction.objects.filter(transaction_type="EXPENSE", date__date=today).aggregate(Sum("amount"))["amount__sum"] or 0,
        "week_income": CashTransaction.objects.filter(transaction_type="INCOME", date__date__gte=start_week).aggregate(Sum("amount"))["amount__sum"] or 0,
        "week_expense": CashTransaction.objects.filter(transaction_type="EXPENSE", date__date__gte=start_week).aggregate(Sum("amount"))["amount__sum"] or 0,
        "total_balance": CashTransaction.objects.order_by('date').last().closing_balance if CashTransaction.objects.exists() else 0,
    }

    # per-account balances
    accounts = {}
    for acc_code, acc_label in Account.ACCOUNT_CHOICES:
        # income = txns.filter(account__code=acc_code, transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
        # expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0
        income = txns.filter(account__code=acc_code, transaction_type="INCOME", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
        expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
        balance = income - expense
        accounts[acc_label] = {"income": income, "expense": expense, "balance": balance}

    return render(request, "cashbook/summary.html", {"summary": summary,"accounts": accounts,"from_date": from_date,
        "to_date": to_date,})

@login_required
def settle_pending(request, txn_id):
    pending_txn = CashTransaction.objects.get(id=txn_id, account__code="PENDING", settled=False)

    if request.method == "POST":
        form = CashTransactionForm(request.POST)
        if form.is_valid():
            settlement = form.save(commit=False)
            settlement.user = request.user

            # balances
            last_txn = CashTransaction.objects.order_by("date").last()
            opening = last_txn.closing_balance if last_txn else 0
            settlement.opening_balance = opening
            if settlement.transaction_type == "INCOME":
                settlement.closing_balance = opening + settlement.amount
            else:
                settlement.closing_balance = opening - settlement.amount

            # link settlement
            settlement.settled_from = pending_txn
            settlement.save()

            # mark pending as settled
            pending_txn.settled = True
            pending_txn.save()
            
            messages.success(request, f"Pending transaction {pending_txn.id} settled to {settlement.account}")
            return redirect("cashbook:transaction_list")
    else:
        form = CashTransactionForm(initial={
            "transaction_type": "INCOME",
            "amount": pending_txn.amount,
            "description": f"Settlement of pending txn {pending_txn.id}"
        })


    return render(request, "cashbook/settle_pending.html", {
        "form": form,
        "pending_txn": pending_txn
    })

@login_required
def product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({"sale_price": float(product.sale_price)})
    except Product.DoesNotExist:
        return JsonResponse({"sale_price": None})