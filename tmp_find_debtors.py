
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')
django.setup()

from debt.models import DebtEntry, AccountType
from accounts.models import Customer
from django.db.models import Sum

def run():
    customers = Customer.objects.all()
    found = False
    
    print("\n--- Partners who owe us but we dont owe them ---")
    print("-" * 60)
    print(f"{'ID':<5} | {'Partner Name':<30} | {'They Owe Us':>15}")
    print("-" * 60)
    
    for c in customers:
        entries = DebtEntry.objects.filter(customer=c)
        r = entries.filter(account_type=AccountType.RECEIVABLE)
        tr = r.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        pr = r.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        rec_bal = round(tr - pr, 0)
        
        p = entries.filter(account_type=AccountType.PAYABLE)
        tp = p.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        pp = p.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        pay_bal = round(tp - pp, 0)
        
        if rec_bal > 0 and pay_bal == 0:
            found = True
            safe_name = c.name.encode('ascii', 'ignore').decode() if c.name else "N/A"
            print(f"{c.id:<5} | {safe_name:<30} | {rec_bal:>15,.0f}")
            
    if not found:
        print("None found.")
    print("-" * 60)

if __name__ == "__main__":
    run()
