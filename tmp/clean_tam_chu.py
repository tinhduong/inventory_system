import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from accounts.models import Customer
from debt.models import Settlement, DebtEntry

def run():
    # Silent find and delete
    targets = Customer.objects.filter(name__icontains='Tâm Chũ')
    
    for c in targets:
        # Delete related payment entries
        DebtEntry.objects.filter(customer=c, is_settlement=True).delete()
        
        # Delete master settlements
        Settlement.objects.filter(customer=c).delete()

if __name__ == '__main__':
    run()
