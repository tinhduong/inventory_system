
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from debt.models import DebtEntry, AccountType
from django.db.models import Sum

customer_id = 2
entries = DebtEntry.objects.filter(customer_id=customer_id)

print(f"--- Customer ID: {customer_id} ---")

# Receivable (Họ nợ mình)
rec_entries = entries.filter(account_type=AccountType.RECEIVABLE)
t_rec = rec_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
p_rec = rec_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
print(f"RECEIVABLE: Total={t_rec}, Paid={p_rec}, Balance={t_rec - p_rec}")

# Payable (Mình nợ họ)
pay_entries = entries.filter(account_type=AccountType.PAYABLE)
t_pay = pay_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
p_pay = pay_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
print(f"PAYABLE: Total={t_pay}, Paid={p_pay}, Balance={t_pay - p_pay}")

print("\n--- Detailed PAYABLE entries (Non-settlement) ---")
for e in pay_entries.filter(is_settlement=False):
    print(f"ID: {e.id}, Date: {e.entry_date or e.created_at}, Amount: {e.amount}, PO: {e.purchase_order_id}")

print("\n--- Detailed PAYABLE entries (Settlement) ---")
for e in pay_entries.filter(is_settlement=True):
    print(f"ID: {e.id}, Date: {e.entry_date or e.created_at}, Amount: {e.amount}, Parent: {e.parent_entry_id}")
