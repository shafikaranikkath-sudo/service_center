from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
  help = 'Create default roles: Admin, Manager, Staff,Agent'


  def handle(self, *args, **kwargs):
    roles = ['Admin', 'Manager', 'Staff', "Agent"]
    for r in roles:
       group, created = Group.objects.get_or_create(name=r)
       if created:
           self.stdout.write(self.style.SUCCESS(f'Created role: {r}'))
       else:
           self.stdout.write(f'Role exists: {r}')
    # (Optional) attach permissions here if you later add granular perms
    self.stdout.write(self.style.SUCCESS('Roles initialized.'))