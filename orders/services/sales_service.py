from django.db import transaction
from django.core.exceptions import ValidationError
from catalog.models import StockItem
from debt.models import DebtEntry, AccountType
from orders.models import OrderStatus

def confirm_sales_order(order):
    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Chỉ có thể xác nhận đơn hàng ở trạng thái Nháp.")

    with transaction.atomic():
        # 1. Update Inventory
        for line in order.lines.all():
            stock, created = StockItem.objects.get_or_create(
                warehouse=order.warehouse,
                product=line.product,
                defaults={'quantity': 0}
            )
            if stock.quantity < line.quantity:
                raise ValidationError(f"Không đủ hàng trong kho cho sản phẩm {line.product.name}. Yêu cầu {line.quantity}, hiện có {stock.quantity}.")
            
            stock.quantity -= line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CONFIRMED
        order.save()

        # 3. Create Debt Entry
        DebtEntry.objects.create(
            customer=order.customer,
            account_type=AccountType.RECEIVABLE,
            sales_order=order,
            amount=order.total_amount,
            is_settlement=False,
            note=f"Ghi nợ từ đơn hàng bán {order.code}"
        )

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

        # 3. Handle Debt (simple approach: create a decrease entry or delete the original)
        # Here we create a settlement-like entry to offset
        DebtEntry.objects.create(
            customer=order.customer,
            account_type=AccountType.RECEIVABLE,
            sales_order=order,
            amount=order.total_amount,
            is_settlement=True,
            note=f"Đối trừ do hủy đơn hàng {order.code}"
        )
