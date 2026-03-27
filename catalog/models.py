from django.db import models

class Warehouse(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Tên kho")
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name="Vị trí")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    def __str__(self):
        return self.name

class Product(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã sản phẩm (SKU)")
    name = models.CharField(max_length=255, verbose_name="Tên sản phẩm")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    unit = models.CharField(max_length=50, verbose_name="Đơn vị tính")
    min_stock = models.IntegerField(default=0, verbose_name="Ngưỡng cảnh báo tồn kho")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class StockItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stocks')
    quantity = models.IntegerField(default=0, verbose_name="Số lượng thực tế")
    held_quantity = models.IntegerField(default=0, verbose_name="Số lượng đang giữ đơn")
    incoming_quantity = models.IntegerField(default=0, verbose_name="Số lượng sắp nhập về")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('warehouse', 'product')
        verbose_name = "Tồn kho"
        verbose_name_plural = "Tồn kho"

    @property
    def available_quantity(self):
        return self.quantity - self.held_quantity

    def __str__(self):
        return f"{self.product.name} tại {self.warehouse.name}: {self.quantity}"
