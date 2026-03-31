import os
import django
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from django.db import transaction
from django.utils import timezone
from orders.models import SalesOrder, OrderStatus
from catalog.models import StockItem
from debt.models import DebtEntry
from orders.services.inventory_service import refresh_stock_reservation

def delete_order_completely(order_id):
    try:
        order = SalesOrder.objects.get(pk=order_id)
    except SalesOrder.DoesNotExist:
        print(f"Order {order_id} not found.")
        return

    with transaction.atomic():
        # print("Deleting order:", order.code)
        warehouse = order.warehouse
        # Use a list to avoid issues after order.lines are gone if CASCADE happens early
        line_data = [(line.product, line.quantity) for line in order.lines.all()]
        
        if order.status == OrderStatus.CONFIRMED:
            for product, quantity in line_data:
                stock = StockItem.objects.filter(warehouse=warehouse, product=product).first()
                if stock:
                    stock.quantity += quantity
                    stock.save()
        
        # Debt
        debt_entries = list(DebtEntry.objects.filter(sales_order=order))
        DebtEntry.objects.filter(parent_entry__in=debt_entries).delete()
        DebtEntry.objects.filter(sales_order=order).delete()

        order.delete()
        print(f"Order {order_id} deleted successfully.")

        # Stock reservation refresh
        for product, _ in line_data:
            refresh_stock_reservation(product, warehouse)

if __name__ == "__main__":
    delete_order_completely(224)
