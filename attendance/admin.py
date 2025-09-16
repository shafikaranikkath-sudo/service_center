from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CheckLog


@admin.register(CheckLog)
class CheckLogAdmin(admin.ModelAdmin):
    list_display = ("user", "check_in_time", "check_out_time")
    list_filter = ("user", "check_in_time")
    search_fields = ("user__username",)