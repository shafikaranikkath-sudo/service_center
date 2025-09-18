

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CashTransaction,Account
from .forms import CashTransactionForm
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta


@login_required
def transaction_list(request):
    if request.user.is_superuser or request.user.groups.filter(name__in=['Admin','Manager']).exists():
        transactions = CashTransaction.objects.all()
    else:
        transactions = CashTransaction.objects.filter(user=request.user)
    return render(request, "cashbook/transaction_list.html", {"transactions": transactions})


@login_required
def transaction_create(request):
    if request.method == "POST":
        form = CashTransactionForm(request.POST)
        if form.is_valid():
            trans = form.save(commit=False)
            trans.user = request.user

            # calculate balances
            last_txn = CashTransaction.objects.order_by('date').last()
            opening = last_txn.closing_balance if last_txn else 0
            trans.opening_balance = opening
            if trans.transaction_type == "INCOME":
                trans.closing_balance = opening + trans.amount
            else:
                trans.closing_balance = opening - trans.amount

            trans.save()
            messages.success(request, "Transaction added successfully!")
            return redirect("cashbook:transaction_list")
    else:
        form = CashTransactionForm()
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
        income = txns.filter(account__code=acc_code, transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
        expense = txns.filter(account__code=acc_code, transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0
        balance = income - expense
        accounts[acc_label] = {"income": income, "expense": expense, "balance": balance}

    return render(request, "cashbook/summary.html", {"summary": summary,"accounts": accounts,"from_date": from_date,
        "to_date": to_date,})

