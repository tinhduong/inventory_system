from django.db import models
from accounts.models import Customer
from orders.models import SalesOrder, PurchaseOrder

class AccountType(models.TextChoices):
    RECEIVABLE = 'RECEIVABLE', 'Phải thu (Khách nợ)'
    PAYABLE = 'PAYABLE', 'Phải trả (Nợ NCC)'

class DebtStatus(models.TextChoices):
    UNPAID = 'UNPAID', 'Chưa thanh toán'
    PARTIAL = 'PARTIAL', 'Thanh toán một phần'
    PAID = 'PAID', 'Đã hoàn tất'

class DebtEntry(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='debt_entries')
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, null=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, null=True, blank=True)
    
    # Liên kết khoản thanh toán này tới khoản nợ nào
    parent_entry = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền")
    is_settlement = models.BooleanField(default=False, verbose_name="Là khoản thanh toán")
    note = models.TextField(blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def paid_amount(self):
        if self.is_settlement: return 0
        # Optimization: Use prefetched payments to avoid N+1 query per row in list views
        if hasattr(self, 'prefetched_payments'):
            return sum(float(p.amount) for p in self.prefetched_payments)
        return self.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def remaining_amount(self):
        if self.is_settlement: return 0
        return self.amount - self.paid_amount

    @property
    def status(self):
        if self.is_settlement: return None
        rem = self.remaining_amount
        if rem <= 0: return DebtStatus.PAID
        if rem < self.amount: return DebtStatus.PARTIAL
        return DebtStatus.UNPAID

    def __str__(self):
        direction = "Giảm" if self.is_settlement else "Tăng"
        return f"{self.customer.name} - {direction} {self.amount}"

class Settlement(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='settlements')
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Số tiền thanh toán")
    payment_date = models.DateField(verbose_name="Ngày thanh toán")
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TT {self.customer.name} - {self.amount_paid}"
