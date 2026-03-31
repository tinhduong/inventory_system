from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from catalog.models import StockItem
from debt.models import DebtEntry, AccountType
from orders.models import OrderStatus

def confirm_sales_order(order):
    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Chỉ có thể xác nhận đơn hàng ở trạng thái Nháp.")

    with transaction.atomic():
        # 0. Check if all lines have unit price
        for line in order.lines.all():
            if line.unit_price is None or line.unit_price < 0:
                raise ValidationError(f"Sản phẩm {line.product.name} chưa có đơn giá. Vui lòng cập nhật đơn giá trước khi xác nhận.")

        # 1. Update Inventory
        for line in order.lines.all():
            stock, created = StockItem.objects.get_or_create(
                warehouse=order.warehouse,
                product=line.product,
                defaults={'quantity': 0}
            )
            # Comment out strict physical stock check to allow negative physical stock
            # if stock.quantity < line.quantity:
            #     raise ValidationError(f"Không đủ hàng trong kho cho sản phẩm {line.product.name}. Yêu cầu {line.quantity}, hiện có {stock.quantity}.")
            
            stock.quantity -= line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CONFIRMED
        order.save()

        # 3. Create Primary Debt Entry
        debt_entry = DebtEntry.objects.create(
            customer=order.customer,
            account_type=AccountType.RECEIVABLE,
            sales_order=order,
            amount=order.total_amount,
            is_settlement=False,
            note=f"Ghi nợ từ đơn hàng bán {order.code}",
            entry_date=order.order_date
        )

        # 4. Handle initial payment if any
        if order.paid_amount > 0:
            DebtEntry.objects.create(
                customer=order.customer,
                account_type=AccountType.RECEIVABLE,
                parent_entry=debt_entry,
                sales_order=order,
                amount=order.paid_amount,
                is_settlement=True,
                note=f"Thanh toán lúc mua cho đơn {order.code}",
                entry_date=order.order_date
            )
        
        # 5. Update Reservation Stock (Clear held stock as it's now deducted from physical)
        from .inventory_service import update_stock_from_order
        update_stock_from_order(order)

def cancel_sales_order(order):
    if order.status != OrderStatus.CONFIRMED:
        raise ValidationError("Chỉ có thể hủy đơn hàng đã xác nhận.")

    with transaction.atomic():
        # 1. Revert Inventory
        for line in order.lines.all():
            stock = StockItem.objects.get(warehouse=order.warehouse, product=line.product)
            stock.quantity += line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CANCELLED
        order.save()

        # 3. Handle Debt
        debt_entry = DebtEntry.objects.filter(sales_order=order, is_settlement=False).first()
        if debt_entry:
            DebtEntry.objects.create(
                customer=order.customer,
                account_type=AccountType.RECEIVABLE,
                parent_entry=debt_entry,
                sales_order=order,
                amount=debt_entry.remaining_amount,
                is_settlement=True,
                note=f"Đối trừ do hủy đơn hàng bán {order.code}",
                entry_date=timezone.now()
            )
        
        # 4. Update Reservation Stock (Release held stock if the order status changed)
        from .inventory_service import update_stock_from_order
        update_stock_from_order(order)
