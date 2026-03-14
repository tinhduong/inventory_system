import os
import django
import sys
from decimal import Decimal
from datetime import date

# Set up Django environment
sys.path.append(r'c:\Users\tinh\Django\StoreManagement_GeminiFlash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Customer
from catalog.models import Warehouse, Product, StockItem
from orders.models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine, OrderStatus
from debt.models import DebtEntry, AccountType

User = get_user_model()

def seed_data():
    print("Starting data seeding...")

    # 1. Create Superuser & Employee
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'role': User.ADMIN,
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("- Created admin/admin123")
    else:
        print("- Admin user already exists")

    employee, _ = User.objects.get_or_create(
        username='nv01',
        defaults={
            'email': 'nv01@example.com',
            'role': User.EMPLOYEE,
            'is_staff': True
        }
    )
    employee.set_password('nv123456')
    employee.save()
    print("- Created employee: nv01/nv123456")

    # 2. Create Warehouses
    kho_chinh, _ = Warehouse.objects.get_or_create(name='Kho Chinh', defaults={'location': 'Ha Noi'})
    kho_phu, _ = Warehouse.objects.get_or_create(name='Kho Phu', defaults={'location': 'TP.HCM'})
    print("- Created 2 warehouses: Kho Chinh, Kho Phu")

    # 3. Create Customers & Suppliers
    ncc_a, _ = Customer.objects.get_or_create(name='Cong ty Dien Tu A', defaults={'is_supplier': True, 'address': 'Ha Noi'})
    ncc_b, _ = Customer.objects.get_or_create(name='Gia Dung B', defaults={'is_supplier': True, 'address': 'Da Nang'})
    kh_an, _ = Customer.objects.get_or_create(name='Nguyen Van An', defaults={'phone': '0987654321', 'address': 'Hai Phong'})
    kh_binh, _ = Customer.objects.get_or_create(name='Tran Thi Binh', defaults={'phone': '0123456789', 'address': 'Can Tho'})
    print("- Created partners: NCC A, NCC B, Khach An, Khach Binh")

    # 4. Create Products
    p1, _ = Product.objects.get_or_create(code='IP15', defaults={'name': 'iPhone 15 Pro Max', 'unit': 'Cai'})
    p2, _ = Product.objects.get_or_create(code='SAM-S24', defaults={'name': 'Samsung Galaxy S24 Ultra', 'unit': 'Cai'})
    p3, _ = Product.objects.get_or_create(code='MAC-M3', defaults={'name': 'MacBook Pro M3', 'unit': 'Cai'})
    print("- Created 3 sample products")

    # 5. Update Inventory
    StockItem.objects.update_or_create(warehouse=kho_chinh, product=p1, defaults={'quantity': 50})
    StockItem.objects.update_or_create(warehouse=kho_chinh, product=p2, defaults={'quantity': 30})
    StockItem.objects.update_or_create(warehouse=kho_phu, product=p3, defaults={'quantity': 20})
    print("- Updated stock quantities")

    # 6. Create Purchase Order
    po = PurchaseOrder.objects.create(
        code='PO-001',
        warehouse=kho_chinh,
        employee=admin_user,
        supplier=ncc_a,
        status=OrderStatus.CONFIRMED,
        order_date=date.today(),
        total_amount=Decimal('100000000')
    )
    PurchaseOrderLine.objects.create(order=po, product=p1, quantity=10, unit_price=Decimal('10000000'))
    print("- Created PO-001")

    # 7. Create Sales Order
    so = SalesOrder.objects.create(
        code='SO-001',
        warehouse=kho_chinh,
        employee=employee,
        customer=kh_an,
        status=OrderStatus.CONFIRMED,
        order_date=date.today(),
        total_amount=Decimal('35000000')
    )
    SalesOrderLine.objects.create(order=so, product=p1, quantity=1, unit_price=Decimal('35000000'))
    print("- Created SO-001")

    # 8. Debt Record
    DebtEntry.objects.get_or_create(
        customer=kh_an,
        account_type=AccountType.RECEIVABLE,
        sales_order=so,
        defaults={'amount': Decimal('35000000'), 'is_settlement': False, 'note': 'Debt from SO-001'}
    )
    print("- Created sample debt for Khach An")

    print("\nSeeding completed!")

if __name__ == "__main__":
    seed_data()
