from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from customers.models import Customer
from products.models import Product

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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cash_transactions")
    date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)

    account = models.ForeignKey("cashbook.Account", on_delete=models.SET_NULL, null=True, blank=True)
      # 🔹 New field: who referred the work
    reference_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_transactions",
        help_text="Select who referred the work (leave empty for Direct)"
    )

       # 🔹 New field: if this is a settlement of a pending transaction
    settled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settlements",
        help_text="Links back to pending transaction if this is a settlement",
    )
    
    settled = models.BooleanField(default=False)  # ✅ marks if pending is settled

    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    # amount will be auto-filled if product selected
    class Meta:
        ordering = ['-date']

    def __str__(self):
        ref = self.reference_user.username if self.reference_user else "Direct"
        return f"{self.transaction_type} {self.amount} ({ref})"
# Create your models here.
