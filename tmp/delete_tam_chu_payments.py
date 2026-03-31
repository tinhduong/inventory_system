import os
import django
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from accounts.models import Customer
from debt.models import DebtEntry, Settlement
from django.db import transaction

def delete_payments_for_customer(customer_name_part):
    customers = Customer.objects.filter(name__icontains=customer_name_part)
    if not customers.exists():
        print(f"Customer matching '{customer_name_part}' not found.")
        return
        
    for customer in customers:
        print(f"Processing customer: {customer.name} (ID: {customer.pk})")
        
        with transaction.atomic():
            # Find and delete overarching settlements
            settlements = Settlement.objects.filter(customer=customer)
            settlement_count = settlements.count()
            print(f"Found {settlement_count} Settlement records.")
            settlements.delete()
            
            # Find and delete DebtEntries where is_settlement=True
            debt_settlements = DebtEntry.objects.filter(customer=customer, is_settlement=True)
            debt_count = debt_settlements.count()
            print(f"Found {debt_count} DebtEntry records (thanh toán/thu nợ).")
            debt_settlements.delete()
            
            print(f"Successfully deleted {settlement_count} Settlement and {debt_count} DebtEntry records for {customer.name}.\n")

if __name__ == "__main__":
    delete_payments_for_customer("Tâm Chữ")
    delete_payments_for_customer("Tâm Chũ")
