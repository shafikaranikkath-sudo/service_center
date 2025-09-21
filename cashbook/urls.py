from django.urls import path
from . import views

app_name = "cashbook"

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("add/", views.transaction_create, name="transaction_create"),
    path("summary/", views.cashbook_summary, name="cashbook_summary"),
    path("settle/<int:txn_id>/", views.settle_pending, name="settle_pending"),
    path("product-price/<int:product_id>/", views.product_price, name="product_price"),
]
