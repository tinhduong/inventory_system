from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Customer
from catalog.models import Warehouse, Product, StockItem
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed demo data for development'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # 1. Create Users
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'role': 'ADMIN', 'is_staff': True, 'is_superuser': True}
        )
        if created: admin.set_password('admin123'); admin.save()

        emp, created = User.objects.get_or_create(
            username='emp',
            defaults={'role': 'EMPLOYEE', 'is_staff': True}
        )
        if created: emp.set_password('emp123'); emp.save()

        # 2. Create Warehouses
        w1, _ = Warehouse.objects.get_or_create(name='Kho Chính', location='Hà Nội')
        w2, _ = Warehouse.objects.get_or_create(name='Kho Phụ', location='TP.HCM')

        # 3. Create Products
        products = []
        for i in range(1, 11):
            p, _ = Product.objects.get_or_create(
                code=f'SKU-{i:03d}',
                defaults={'name': f'Sản phẩm {i}', 'unit': 'Cái', 'description': f'Mô tả cho sp {i}'}
            )
            products.append(p)

        # 4. Create Partners
        for i in range(1, 11):
            Customer.objects.get_or_create(
                name=f'Đối tác {i}',
                defaults={'phone': f'0987000{i}', 'address': f'Địa chỉ {i}'}
            )

        # 5. Initial Stock
        for p in products:
            StockItem.objects.get_or_create(warehouse=w1, product=p, defaults={'quantity': 50})
            StockItem.objects.get_or_create(warehouse=w2, product=p, defaults={'quantity': 20})

        self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        self.stdout.write(f"Admin: admin / admin123")
        self.stdout.write(f"Employee: emp / emp123")
