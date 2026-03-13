from django.db import models
from accounts.models import Customer
from orders.models import SalesOrder, PurchaseOrder

class AccountType(models.TextChoices):
    RECEIVABLE = 'RECEIVABLE', 'Phải thu (Khách nợ)'
    PAYABLE = 'PAYABLE', 'Phải trả (Nợ NCC)'

class DebtEntry(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debt_entries')
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền")
    # Increase or Decrease
    is_settlement = models.BooleanField(default=False, verbose_name="Là khoản thanh toán")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        direction = "Giảm" if self.is_settlement else "Tăng"
        return f"{self.customer.name} - {self.get_account_type_display()} - {direction} {self.amount}"

class Settlement(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='settlements')
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền thanh toán")
    payment_date = models.DateField(verbose_name="Ngày thanh toán")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TT {self.customer.name} - {self.amount_paid}"
