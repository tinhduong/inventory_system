from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from catalog.models import Warehouse, Product, StockItem
from orders.models import SalesOrder, PurchaseOrder
from accounts.models import Customer
from django.db.models import Sum

from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard(request):
    period = request.GET.get('period', 'all')
    
    # Base querysets
    sales_qs = SalesOrder.objects.filter(status='CONFIRMED')
    purchase_qs = PurchaseOrder.objects.filter(status='CONFIRMED')
    
    # Filter by period
    today = timezone.localtime(timezone.now()).date()
    yesterday = today - timedelta(days=1)
    
    start_date = None
    end_date = None
    
    if period == 'today':
        start_date = today
    elif period == 'yesterday':
        start_date = yesterday
        end_date = today
    elif period == '7d':
        start_date = today - timedelta(days=7)
    elif period == '1m':
        start_date = today - timedelta(days=30)
    elif period == '3m':
        start_date = today - timedelta(days=90)
    elif period == '6m':
        start_date = today - timedelta(days=180)
    elif period == '1y':
        start_date = today - timedelta(days=365)
        
    if start_date:
        sales_qs = sales_qs.filter(order_date__gte=start_date)
        purchase_qs = purchase_qs.filter(order_date__gte=start_date)
    
    if end_date:
        sales_qs = sales_qs.filter(order_date__lt=end_date)
        purchase_qs = purchase_qs.filter(order_date__lt=end_date)

    context = {
        'warehouse_count': Warehouse.objects.count(),
        'product_count': Product.objects.count(),
        'customer_count': Customer.objects.count(),
        'total_sales': sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'total_purchases': purchase_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'recent_sales': sales_qs.order_by('-created_at')[:5],
        'recent_purchases': purchase_qs.order_by('-created_at')[:5],
        'current_period': period,
    }
    return render(request, 'dashboard.html', context)
