import os
import django
import sys

# Set up Django environment
sys.path.append(r'c:\Users\tinh\Django\StoreManagement_GeminiFlash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from debt.models import DebtEntry, AccountType
from orders.models import PurchaseOrder, SalesOrder
from accounts.models import Customer

def inspect_customer(name_part):
    customers = Customer.objects.filter(name__icontains=name_part)
    for c in customers:
        print(f"--- Customer: {c.name} (ID: {c.id}) ---")
        
        entries = DebtEntry.objects.filter(customer=c)
        print(f"Debt Entries Count: {entries.count()}")
        for e in entries:
            # Print with ASCII only to avoid terminal encoding issues
            note_safe = "".join([char if ord(char) < 128 else "?" for char in (e.note or "")])
            print(f"  ID: {e.id}, Type: {e.account_type}, Settlement: {e.is_settlement}, Amount: {e.amount}, Parent: {e.parent_entry_id}, Note: {note_safe}")
        
        pos = PurchaseOrder.objects.filter(supplier=c)
        print(f"Purchase Orders Count: {pos.count()}")
        for po in pos:
            print(f"  PO Code: {po.code}, Status: {po.status}, Total: {po.total_amount}")

        sos = SalesOrder.objects.filter(customer=c)
        print(f"Sales Orders Count: {sos.count()}")
        for so in sos:
            print(f"  SO Code: {so.code}, Status: {so.status}, Total: {so.total_amount}")

if __name__ == "__main__":
    inspect_customer("Dien Tu A")
