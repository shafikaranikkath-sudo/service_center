from django import forms
from .models import CashTransaction
from customers.models import Customer
from products.models import Product

class CashTransactionForm(forms.ModelForm):
    class Meta:
        model = CashTransaction
        fields = ['transaction_type', 'account', 'product', 'amount', 'description', 'reference_user', 'customer']
        # fields = ['transaction_type', 'amount', 'description', 'account','reference_user','customer']