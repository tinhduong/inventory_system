from django.db import transaction
from django.core.exceptions import ValidationError
from catalog.models import StockItem
from debt.models import DebtEntry, AccountType
from orders.models import OrderStatus

def confirm_purchase_order(order):
    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Chỉ có thể xác nhận đơn nhập ở trạng thái Nháp.")

    with transaction.atomic():
        # 1. Update Inventory
        for line in order.lines.all():
            stock, created = StockItem.objects.get_or_create(
                warehouse=order.warehouse,
                product=line.product,
                defaults={'quantity': 0}
            )
            stock.quantity += line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CONFIRMED
        order.save()

        # 3. Create Primary Debt Entry
        debt_entry = DebtEntry.objects.create(
            customer=order.supplier,
            account_type=AccountType.PAYABLE,
            purchase_order=order,
            amount=order.total_amount,
            is_settlement=False,
            note=f"Ghi nợ từ đơn hàng nhập {order.code}"
        )

        # 4. Handle initial payment if any
        if order.paid_amount > 0:
            DebtEntry.objects.create(
                customer=order.supplier,
                account_type=AccountType.PAYABLE,
                parent_entry=debt_entry,
                purchase_order=order,
                amount=order.paid_amount,
                is_settlement=True,
                note=f"Thanh toán lúc nhập đơn {order.code}"
            )

def cancel_purchase_order(order):
    if order.status != OrderStatus.CONFIRMED:
        raise ValidationError("Chỉ có thể hủy đơn nhập đã xác nhận.")

    with transaction.atomic():
        # 1. Revert Inventory
        for line in order.lines.all():
            stock = StockItem.objects.get(warehouse=order.warehouse, product=line.product)
            if stock.quantity < line.quantity:
                raise ValidationError(f"Không thể hủy đơn nhập: Tồn kho hiện tại của {line.product.name} ({stock.quantity}) ít hơn số lượng cần trừ ({line.quantity}).")
            stock.quantity -= line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CANCELLED
        order.save()

        # 3. Handle Debt (offset entry)
        DebtEntry.objects.create(
            customer=order.supplier,
            account_type=AccountType.PAYABLE,
            purchase_order=order,
            amount=order.total_amount,
            is_settlement=True,
            note=f"Đối trừ do hủy đơn hàng nhập {order.code}"
        )
