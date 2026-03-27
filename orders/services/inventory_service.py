from django.db.models import Sum
from django.db import transaction
from catalog.models import StockItem
from orders.models import SalesOrderLine, PurchaseOrderLine, OrderStatus

def refresh_stock_reservation(product, warehouse):
    """
    Cập nhật lại số lượng giữ hàng (held) và hàng sắp về (incoming) cho một sản phẩm tại kho.
    """
    # 1. Tính tổng giữ hàng từ các Đơn bán đang ở trạng thái Nháp
    held = SalesOrderLine.objects.filter(
        order__status=OrderStatus.DRAFT,
        product=product,
        order__warehouse=warehouse
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # 2. Tính tổng hàng sắp về từ các Đơn nhập đang ở trạng thái Nháp
    incoming = PurchaseOrderLine.objects.filter(
        order__status=OrderStatus.DRAFT,
        product=product,
        order__warehouse=warehouse
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # 3. Cập nhật vào StockItem
    stock, created = StockItem.objects.get_or_create(
        product=product,
        warehouse=warehouse,
        defaults={'quantity': 0}
    )
    stock.held_quantity = held
    stock.incoming_quantity = incoming
    stock.save()
    return stock

def update_stock_from_order(order):
    """
    Cập nhật lại giữ hàng/sắp về cho tất cả sản phẩm trong một đơn hàng.
    """
    products = set()
    if hasattr(order, 'lines'):
        for line in order.lines.all():
            products.add(line.product)
    
    for product in products:
        refresh_stock_reservation(product, order.warehouse)
