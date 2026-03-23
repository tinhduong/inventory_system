
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from accounts.models import Customer
for c in Customer.objects.all():
    print(f"ID: {c.id}, Name: {c.name}")
