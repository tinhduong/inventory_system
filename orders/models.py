import uuid
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils import timezone
from accounts.models import Customer
from catalog.models import Warehouse, Product
import vnlunar

def solar_to_lunar_string(solar_date):
    if not solar_date:
        return ""
    lunar = vnlunar.get_lunar_date(solar_date.day, solar_date.month, solar_date.year)
    leap = " (Nhuận)" if lunar['leap'] else ""
    return f"{lunar['day']:02d}/{lunar['month']:02d}/{lunar['year']}{leap}"

class OrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Nháp'
    CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
    CANCELLED = 'CANCELLED', 'Đã hủy'

class SalesOrder(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã đơn hàng")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="Kho xuất")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Nhân viên")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Đối tác")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT, verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_date = models.DateField(default=timezone.now, verbose_name="Ngày đặt hàng")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, verbose_name="Tổng tiền")
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, verbose_name="Đã thanh toán (tại quầy)")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    @property
    def lunar_date_display(self):
        return solar_to_lunar_string(self.order_date)

    @property
    def remaining_amount(self):
        if self.status == OrderStatus.CANCELLED:
            return 0
        # Ưu tiên lấy từ công nợ nếu đã xác nhận
        if self.status == OrderStatus.CONFIRMED:
            entry = self.debt_entry
            return entry.remaining_amount if entry else 0
        return self.total_amount - self.paid_amount

    @property
    def current_paid_amount(self):
        if self.status == OrderStatus.CANCELLED:
            # Nếu hủy, tiền "đã trả" coi như là 0 trên chế độ xem đơn hàng 
            # (Thực tế tiền có thể đã vào sổ nợ như một khoản dư)
            return 0
        return self.total_amount - self.remaining_amount

    @property
    def debt_status_display(self):
        if self.status == OrderStatus.CANCELLED:
            return "Đã hủy"
        entry = self.debt_entry
        if not entry or not entry.status:
            return "N/A"
        return entry.status.label

    def save(self, *args, **kwargs):
        if not self.code:
            from orders.forms import generate_order_code
            self.code = generate_order_code('SO', SalesOrder, self.order_date)
        super().save(*args, **kwargs)

    @property
    def debt_entry(self):
        # Optimization: Check if already prefetched to avoid N+1 queries
        if hasattr(self, 'prefetched_debt_entries'):
            return self.prefetched_debt_entries[0] if self.prefetched_debt_entries else None
        from debt.models import DebtEntry
        return DebtEntry.objects.filter(sales_order=self, is_settlement=False).first()

    def get_payment_history(self):
        history = []
        if self.paid_amount > 0:
            history.append({
                'date': self.created_at,
                'amount': self.paid_amount,
                'type': 'Thanh toán ban đầu',
                'note': 'Đã trả khi tạo đơn'
            })
        
        entry = self.debt_entry
        if entry:
            for p in entry.payments.all().select_related('settlement'):
                history.append({
                    'date': p.entry_date or p.created_at,
                    'amount': p.amount,
                    'type': 'Trả nợ / Quyết toán',
                    'note': p.note or (p.settlement.note if p.settlement else "")
                })
        history.sort(key=lambda x: x['date'], reverse=True)
        return history

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Đơn bán hàng"
        verbose_name_plural = "Đơn bán hàng"

class SalesOrderLine(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Sản phẩm")
    quantity = models.IntegerField(verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Đơn giá", null=True, blank=True)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * (self.unit_price or 0)
        super().save(*args, **kwargs)

class PurchaseOrder(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã đơn nhập")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="Kho nhập")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Nhân viên")
    supplier = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Nhà cung cấp")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT, verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_date = models.DateField(default=timezone.now, verbose_name="Ngày nhập hàng")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, verbose_name="Tổng tiền")
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, blank=True, verbose_name="Đã thanh toán (tại quầy)")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True)

    @property
    def lunar_date_display(self):
        return solar_to_lunar_string(self.order_date)

    @property
    def remaining_amount(self):
        if self.status == OrderStatus.CANCELLED:
            return 0
        if self.status == OrderStatus.CONFIRMED:
            entry = self.debt_entry
            return entry.remaining_amount if entry else 0
        return self.total_amount - self.paid_amount

    @property
    def current_paid_amount(self):
        if self.status == OrderStatus.CANCELLED:
            return 0
        return self.total_amount - self.remaining_amount

    @property
    def debt_status_display(self):
        if self.status == OrderStatus.CANCELLED:
            return "Đã hủy"
        entry = self.debt_entry
        if not entry or not entry.status:
            return "N/A"
        return entry.status.label

    def save(self, *args, **kwargs):
        if not self.code:
            from orders.forms import generate_order_code
            self.code = generate_order_code('PO', PurchaseOrder, self.order_date)
        super().save(*args, **kwargs)

    @property
    def debt_entry(self):
        # Optimization: Check if already prefetched to avoid N+1 queries
        if hasattr(self, 'prefetched_debt_entries'):
            return self.prefetched_debt_entries[0] if self.prefetched_debt_entries else None
        from debt.models import DebtEntry
        return DebtEntry.objects.filter(purchase_order=self, is_settlement=False).first()

    def get_payment_history(self):
        history = []
        if self.paid_amount > 0:
            history.append({
                'date': self.created_at,
                'amount': self.paid_amount,
                'type': 'Thanh toán ban đầu',
                'note': 'Đã trả khi tạo đơn'
            })
        
        entry = self.debt_entry
        if entry:
            for p in entry.payments.all().select_related('settlement'):
                history.append({
                    'date': p.entry_date or p.created_at,
                    'amount': p.amount,
                    'type': 'Trả nợ / Quyết toán',
                    'note': p.note or (p.settlement.note if p.settlement else "")
                })
        history.sort(key=lambda x: x['date'], reverse=True)
        return history

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Đơn nhập hàng"
        verbose_name_plural = "Đơn nhập hàng"

class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Sản phẩm")
    quantity = models.IntegerField(verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Đơn giá", null=True, blank=True)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * (self.unit_price or 0)
        super().save(*args, **kwargs)

class OrderLog(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='logs', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người thực hiện")
    action = models.CharField(max_length=255, verbose_name="Hành động")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lịch sử đơn hàng"
        verbose_name_plural = "Lịch sử đơn hàng"
