
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from debt.models import DebtEntry, AccountType
from django.db.models import Sum

customer_id = 2
entries = DebtEntry.objects.filter(customer_id=customer_id)

print(f"--- Detailed RECEIVABLE entries (Non-settlement) ---")
for e in entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=False):
    print(f"ID: {e.id}, Date: {e.entry_date or e.created_at}, Amount: {e.amount}, SO: {e.sales_order_id}")

print("\n--- Detailed RECEIVABLE entries (Settlement) ---")
for e in entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=True):
    print(f"ID: {e.id}, Date: {e.entry_date or e.created_at}, Amount: {e.amount}, Parent: {e.parent_entry_id}")
