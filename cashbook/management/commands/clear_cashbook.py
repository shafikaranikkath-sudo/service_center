from django.core.management.base import BaseCommand
from cashbook.models import CashTransaction

class Command(BaseCommand):
    help = "Clear all transactions from Cashbook"

    def handle(self, *args, **kwargs):
        count, _ = CashTransaction.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} transactions from Cashbook."))
