from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from catalog.models import Warehouse, Product, StockItem
from orders.models import SalesOrder, PurchaseOrder
from accounts.models import Customer
from django.db.models import Sum

@login_required
def dashboard(request):
    context = {
        'warehouse_count': Warehouse.objects.count(),
        'product_count': Product.objects.count(),
        'customer_count': Customer.objects.count(),
        'total_sales': SalesOrder.objects.filter(status='CONFIRMED').aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'recent_sales': SalesOrder.objects.order_by('-created_at')[:5],
        'recent_purchases': PurchaseOrder.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard.html', context)
