from django import forms
from .models import CashTransaction

class CashTransactionForm(forms.ModelForm):
    class Meta:
        model = CashTransaction
        fields = ['transaction_type', 'amount', 'description', 'account','reference_user']