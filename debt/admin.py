from django.contrib import admin
from .models import DebtEntry, Settlement

@admin.register(DebtEntry)
class DebtEntryAdmin(admin.ModelAdmin):
    list_display = ['customer', 'account_type', 'amount', 'is_settlement', 'created_at']
    list_filter = ['account_type', 'is_settlement']
    search_fields = ['customer__name']

@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ['customer', 'account_type', 'amount_paid', 'payment_date']
    list_filter = ['account_type']
    search_fields = ['customer__name']
