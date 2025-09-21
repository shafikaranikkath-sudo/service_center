from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Customer
from .forms import CustomerForm
from cashbook.models import CashTransaction
from django.db.models import Sum

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, "customers/customer_list.html", {"customers": customers})

@login_required
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer added successfully")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm()
    return render(request, "customers/customer_form.html", {"form": form})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    transactions = CashTransaction.objects.filter(customer=customer).order_by("-date")

    # Aggregate totals
    total_income = transactions.filter(transaction_type="INCOME").aggregate(Sum("amount"))["amount__sum"] or 0
    total_expense = transactions.filter(transaction_type="EXPENSE").aggregate(Sum("amount"))["amount__sum"] or 0
    balance = total_income - total_expense

    return render(request, "customers/customer_detail.html", {
        "customer": customer,
        "transactions": transactions,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
    })

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated successfully")
            return redirect("customers:customer_list")
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customers/customer_form.html", {"form": form, "edit": True})

@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully")
        return redirect("customers:customer_list")
    return render(request, "customers/customer_confirm_delete.html", {"customer": customer})