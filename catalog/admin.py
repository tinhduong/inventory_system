from django.contrib import admin
from .models import Warehouse, Product, StockItem

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active']
    list_filter = ['is_active']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'unit', 'created_at']
    search_fields = ['code', 'name']

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ['warehouse', 'product', 'quantity']
    list_filter = ['warehouse', 'product']
