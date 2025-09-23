

# Create your views here.
from django.shortcuts import get_object_or_404, render, redirect
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
    
    # ✅ Exclude unsettled Pending for all income/expense/balance
    # base_qs = txns.exclude(account__code="PENDING", settled=False)
    base_qs = txns.exclude(account__code="PENDING")
    summary = {
    "today_income": base_qs.filter(transaction_type="INCOME", date__date=today).aggregate(Sum("amount"))["amount__sum"] or 0,
    "today_expense": base_qs.filter(transaction_type="EXPENSE", date__date=today).aggregate(Sum("amount"))["amount__sum"] or 0,
    "week_income": base_qs.filter(transaction_type="INCOME", date__date__gte=start_week).aggregate(Sum("amount"))["amount__sum"] or 0,
    "week_expense": base_qs.filter(transaction_type="EXPENSE", date__date__gte=start_week).aggregate(Sum("amount"))["amount__sum"] or 0,
    "total_balance": base_qs.order_by("date").last().closing_balance if base_qs.exists() else 0,

    # ✅ Pending tracked separately (only unsettled)
    "pending_total": txns.filter(account__code="PENDING", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0,
    }


    # # per-account balances
    # accounts = {}
    # for acc_code, acc_label in Account.ACCOUNT_CHOICES:
    #     if acc_code == "PENDING":
    #         # ✅ Show unsettled transactions for Pending account
    #         income = txns.filter(account__code=acc_code, transaction_type="INCOME", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
    #         expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
    #     else:
    #         # income = txns.filter(account__code=acc_code, transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
    #         # expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0
    #         # income = txns.filter(account__code=acc_code, transaction_type="INCOME", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
    #         # expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
    #         real_txns = txns.exclude(account__code="PENDING", settled=False)

    #         income = real_txns.filter(transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
    #         expense = real_txns.filter(transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0
    #         balance = income - expense
    #         # Track pending separately
    #     pending_total = txns.filter(account__code="PENDING", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
    #     accounts[acc_label] = {"income": income, "expense": expense, "balance": balance}
    accounts = {}
    total_income = 0
    total_expense = 0

    for acc_code, acc_label in Account.ACCOUNT_CHOICES:
        if acc_code == "PENDING":
            # Only unsettled pending transactions
            income = txns.filter(account__code=acc_code, transaction_type="INCOME", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
            expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
        else:
            # Exclude unsettled pending from normal accounts
            acc_txns = txns.filter(account__code=acc_code).exclude(account__code="PENDING", settled=False)
            income = acc_txns.filter(transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
            expense = acc_txns.filter(transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0

            # 👈 Add to global totals (excluding pending)
            total_income += income
            total_expense += expense

        balance = income - expense
        accounts[acc_label] = {"income": income, "expense": expense, "balance": balance}

        pending_total = txns.filter(account__code="PENDING", settled=False).aggregate(Sum("amount"))["amount__sum"] or 0
        closing_balance = total_income - total_expense

    return render(request, "cashbook/summary.html", {"summary": summary,"accounts": accounts,"from_date": from_date,
        "to_date": to_date,"income": total_income,"expense": total_expense,"closing_balance": closing_balance,
        "pending_total": pending_total,})

@login_required
def settle_pending(request, pk):
    txn = get_object_or_404(CashTransaction, pk=pk, account__code="PENDING", settled=False)

    if request.method == "POST":
        target_account_code = request.POST.get("account")
        if target_account_code:
            try:
                target_account = Account.objects.get(code=target_account_code)
                txn.account = target_account
                txn.settled = True
                txn.save()
                messages.success(request, f"Pending transaction settled to {target_account.get_code_display()}")
            except Account.DoesNotExist:
                messages.error(request, "Invalid account selected for settlement")
        return redirect("cashbook:transaction_list")

    accounts = Account.objects.exclude(code="PENDING")
    return render(request, "cashbook/settle_form.html", {"txn": txn, "accounts": accounts})
@login_required
def product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({"sale_price": float(product.sale_price)})
    except Product.DoesNotExist:
        return JsonResponse({"sale_price": None})