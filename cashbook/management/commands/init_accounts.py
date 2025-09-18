from django.core.management.base import BaseCommand
from cashbook.models import Account

class Command(BaseCommand):
    help = "Initialize default accounts"

    def handle(self, *args, **kwargs):
        accounts = [
            ("CASH", "Cash Account"),
            ("BANK", "Bank/GPay Account"),
            ("PENDING", "Pending Account"),
        ]
        for code, desc in accounts:
            acc, created = Account.objects.get_or_create(code=code, defaults={"description": desc})
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created account: {desc}"))
            else:
                self.stdout.write(f"Account exists: {desc}")
