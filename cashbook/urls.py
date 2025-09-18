from django.urls import path
from . import views

app_name = "cashbook"

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("add/", views.transaction_create, name="transaction_create"),
    path("summary/", views.cashbook_summary, name="cashbook_summary"),
]
