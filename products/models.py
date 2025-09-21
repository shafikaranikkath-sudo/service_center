from django.db import models

class Product(models.Model):
    PRODUCT_TYPES = [
        ("PRODUCT", "Product"),
        ("SERVICE", "Service"),
    ]

    type = models.CharField(max_length=10, choices=PRODUCT_TYPES)
    item = models.CharField(max_length=200)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item} ({self.type})"
