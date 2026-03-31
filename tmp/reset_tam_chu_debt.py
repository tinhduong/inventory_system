import os
import django
import sys

sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from debt.models import DebtEntry, Settlement
from accounts.models import Customer
from django.db import transaction

def cleanup_tam_chu():
    try:
        # Tìm khách hàng theo ID hoặc Tên không dấu để an toàn
        customer = Customer.objects.filter(name__icontains='Tâm Chũ').first()
        if not customer:
            print("Customer not found.")
            return

        print(f"Cleaning for customer ID: {customer.id}")
        
        with transaction.atomic():
            # 1. Xóa Settlements
            settlements = Settlement.objects.filter(customer=customer)
            s_count = settlements.count()
            settlements.delete()
            print(f"Deleted {s_count} settlements.")
            
            # 2. Xóa DebtEntry payments
            payments = DebtEntry.objects.filter(customer=customer, is_settlement=True)
            p_count = payments.count()
            payments.delete()
            print(f"Deleted {p_count} debt entry payments.")
        
        print("Success.")
    except Exception as e:
        print(f"Error occurred.")

if __name__ == "__main__":
    cleanup_tam_chu()
