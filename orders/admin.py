from django.contrib import admin
from .models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine

class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'warehouse']
    search_fields = ['code', 'customer__name']
    inlines = [SalesOrderLineInline]

class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'supplier', 'status', 'total_amount', 'order_date']
    list_filter = ['status', 'warehouse']
    search_fields = ['code', 'supplier__name']
    inlines = [PurchaseOrderLineInline]
