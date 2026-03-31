from django.db import models
from django.utils import timezone
from accounts.models import Customer
from orders.models import SalesOrder, PurchaseOrder


class AccountType(models.TextChoices):
    """Defines the direction of the debt (Receivable or Payable)."""
    RECEIVABLE = 'RECEIVABLE', 'Phải thu (Khách nợ)'
    PAYABLE = 'PAYABLE', 'Phải trả (Nợ NCC)'


class DebtStatus(models.TextChoices):
    """Represents the payment status of a specific debt entry."""
    UNPAID = 'UNPAID', 'Chưa thanh toán'
    PARTIAL = 'PARTIAL', 'Thanh toán một phần'
    PAID = 'PAID', 'Đã hoàn tất'


class DebtEntry(models.Model):
    """
    Core ledger entry. Can be an original debt (is_settlement=False) 
    or a payment/deduction (is_settlement=True).
    """
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='debt_entries')
    account_type = models.CharField(
        max_length=20, choices=AccountType.choices)
    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.PROTECT, null=True, blank=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.PROTECT, null=True, blank=True)
    
    # Links this allocation/payment to the original debt entry
    parent_entry = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True, 
        related_name='payments')
    
    # Associated master settlement record (for FIFO groupings)
    settlement = models.ForeignKey(
        'Settlement', on_delete=models.CASCADE, null=True, blank=True, 
        related_name='entries')
    
    amount = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Số tiền")
    is_settlement = models.BooleanField(
        default=False, verbose_name="Là khoản thanh toán")
    note = models.TextField(
        blank=True, null=True, verbose_name="Ghi chú")
    entry_date = models.DateTimeField(
        default=None, null=True, blank=True, verbose_name="Ngày ghi")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def paid_amount(self):
        """Calculates total paid amount for this specific debt entry."""
        if self.is_settlement:
            return 0
        return self.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def remaining_amount(self):
        """Calculates remaining debt balance."""
        if self.is_settlement:
            return 0
        return self.amount - self.paid_amount

    @property
    def status(self):
        """Standardized debt status based on payment progress."""
        if self.is_settlement:
            return None
        rem = self.remaining_amount
        if rem <= 0:
            return DebtStatus.PAID
        if rem < self.amount:
            return DebtStatus.PARTIAL
        return DebtStatus.UNPAID

    def __str__(self):
        direction = "Giảm (-)" if self.is_settlement else "Tăng (+)"
        return f"{self.customer.name} - {direction} {self.amount:,.0f}"

    class Meta:
        verbose_name = "Bản ghi công nợ"
        verbose_name_plural = "Bản ghi công nợ"


class Settlement(models.Model):
    """
    Master record for a bulk payment or deduction transaction.
    Usually groups multiple DebtEntry allocations together.
    """
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name='settlements')
    account_type = models.CharField(
        max_length=20, choices=AccountType.choices)
    amount_paid = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Số tiền thanh toán")
    payment_date = models.DateField(
        verbose_name="Ngày thanh toán")
    note = models.TextField(
        blank=True, null=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TT #{self.id} - {self.customer.name} ({self.amount_paid:,.0f})"

    class Meta:
        verbose_name = "Phiếu quyết toán"
        verbose_name_plural = "Phiếu quyết toán"
