from django.db import models
from django.contrib.auth.models import User


class Account(models.Model):

    ACCOUNT_CHOICES = [
        ("CASH", "Cash Account"),
        ("BANK", "Bank/GPay Account"),
        ("PENDING", "Pending Account"),
    ]
    code = models.CharField(max_length=20, choices=ACCOUNT_CHOICES, unique=True,default="CASH")
    description = models.TextField(blank=True)

    def __str__(self):
        return dict(self.ACCOUNT_CHOICES).get(self.code, self.code)

class CashTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cash_transactions")
    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)


    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)

    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} by {self.account}"    
# Create your models here.
