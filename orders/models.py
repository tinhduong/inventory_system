import uuid
from django.db import models
from django.conf import settings
from accounts.models import Customer
from catalog.models import Warehouse, Product

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
    order_date = models.DateField(verbose_name="Ngày đặt hàng")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Tổng tiền")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def save(self, *args, **kwargs):
        if not self.code:
            from orders.forms import generate_order_code
            self.code = generate_order_code('SO', SalesOrder)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Đơn bán hàng"
        verbose_name_plural = "Đơn bán hàng"

class SalesOrderLine(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Sản phẩm")
    quantity = models.IntegerField(verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Đơn giá")
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class PurchaseOrder(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã đơn nhập")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, verbose_name="Kho nhập")
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, verbose_name="Nhân viên")
    supplier = models.ForeignKey(Customer, on_delete=models.PROTECT, verbose_name="Nhà cung cấp")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT, verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_date = models.DateField(verbose_name="Ngày nhập hàng")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Tổng tiền")
    public_token = models.UUIDField(default=uuid.uuid4, unique=True)

    def save(self, *args, **kwargs):
        if not self.code:
            from orders.forms import generate_order_code
            self.code = generate_order_code('PO', PurchaseOrder)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = "Đơn nhập hàng"
        verbose_name_plural = "Đơn nhập hàng"

class PurchaseOrderLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name="Sản phẩm")
    quantity = models.IntegerField(verbose_name="Số lượng")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Đơn giá")
    line_total = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
