from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from catalog.models import StockItem
from debt.models import DebtEntry, AccountType
from orders.models import OrderStatus

def confirm_purchase_order(order):
    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Chỉ có thể xác nhận đơn nhập ở trạng thái Nháp.")

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
            note=f"Ghi nợ từ đơn hàng nhập {order.code}",
            entry_date=order.order_date
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
                note=f"Thanh toán lúc nhập đơn {order.code}",
                entry_date=order.order_date
            )
        
        # 5. Update Reservation Stock (Clear incoming as it's now in physical)
        from .inventory_service import update_stock_from_order
        update_stock_from_order(order)

def cancel_purchase_order(order):
    if order.status != OrderStatus.CONFIRMED:
        raise ValidationError("Chỉ có thể hủy đơn nhập đã xác nhận.")

    with transaction.atomic():
        # 1. Revert Inventory
        for line in order.lines.all():
            stock = StockItem.objects.get(warehouse=order.warehouse, product=line.product)
            # Comment out check for canceling purchase order to allow negative stock
            # if stock.quantity < line.quantity:
            #     raise ValidationError(f"Không thể hủy đơn nhập: Tồn kho hiện tại của {line.product.name} ({stock.quantity}) ít hơn số lượng cần trừ ({line.quantity}).")
            stock.quantity -= line.quantity
            stock.save()

        # 2. Update Order Status
        order.status = OrderStatus.CANCELLED
        order.save()

        # 3. Handle Debt
        debt_entry = DebtEntry.objects.filter(purchase_order=order, is_settlement=False).first()
        if debt_entry:
            DebtEntry.objects.create(
                customer=order.supplier,
                account_type=AccountType.PAYABLE,
                parent_entry=debt_entry,
                purchase_order=order,
                amount=debt_entry.remaining_amount,
                is_settlement=True,
                note=f"Đối trừ do hủy đơn hàng nhập {order.code}",
                entry_date=timezone.now()
            )
        else:
            # Fallback if debt entry is not found for some reason (unlikely)
            DebtEntry.objects.create(
                customer=order.supplier,
                account_type=AccountType.PAYABLE,
                purchase_order=order,
                amount=order.total_amount,
                is_settlement=True,
                note=f"Đối trừ do hủy đơn hàng nhập {order.code}",
                entry_date=timezone.now()
            )
        
        # 4. Update Reservation Stock
        from .inventory_service import update_stock_from_order
        update_stock_from_order(order)
