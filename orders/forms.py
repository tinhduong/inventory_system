from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine
from catalog.models import StockItem

def generate_order_code(prefix, model_class, date=None):
    if not date:
        date = timezone.now()
    date_str = date.strftime('%y%m%d')
    # Tìm mã đơn hàng cao nhất trong ngày đó
    last_order = model_class.objects.filter(code__startswith=f"{prefix}{date_str}").order_by('-code').first()
    
    if last_order:
        last_num = int(last_order.code.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
        
    return f"{prefix}{date_str}-{new_num:03d}"

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['warehouse', 'customer', 'order_date', 'paid_amount']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
            'customer': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control money-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_amount'].required = False
        # Nếu chỉ có 1 kho, mặc định chọn và disable
        from catalog.models import Warehouse
        wh = Warehouse.objects.first()
        if wh:
            self.fields['warehouse'].initial = wh
            # Nếu chỉ có 1 kho duy nhất trong hệ thống thì disable chọn kho
            if Warehouse.objects.count() <= 1:
                self.fields['warehouse'].disabled = True

class BaseSalesOrderLineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        warehouse = self.instance.warehouse if hasattr(self.instance, 'warehouse') else None
        
        # Lấy kho cũ nếu đang sửa đơn hàng để đối chiếu
        original_warehouse = None
        if self.instance.pk:
            try:
                original_warehouse = SalesOrder.objects.get(pk=self.instance.pk).warehouse
            except SalesOrder.DoesNotExist:
                pass

        for form in self.forms:
            if not form.is_valid() or (self.can_delete and self._should_delete_form(form)):
                continue
            
            product = form.cleaned_data.get('product')
            quantity = form.cleaned_data.get('quantity')
            
            if product and quantity and warehouse:
                stock = StockItem.objects.filter(product=product, warehouse=warehouse).first()
                available = stock.available_quantity if stock else 0
                
                # Nếu là sửa dòng đã có VÀ kho không đổi, cộng lại số lượng của chính dòng đó vào khả dụng
                current_line_qty = 0
                if form.instance.pk and warehouse == original_warehouse:
                    try:
                        current_line_qty = SalesOrderLine.objects.get(pk=form.instance.pk).quantity
                    except SalesOrderLine.DoesNotExist:
                        pass
                
                if quantity > (available + current_line_qty):
                    form.add_error('quantity', f"Số lượng ({quantity}) vượt quá tồn kho khả dụng ({available + current_line_qty}).")

SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder, SalesOrderLine,
    formset=BaseSalesOrderLineFormSet,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input'}),
        'unit_price': forms.TextInput(attrs={'class': 'form-control money-input price-input'}),
    },
    extra=1, can_delete=True
)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['warehouse', 'supplier', 'order_date', 'paid_amount']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
            'supplier': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control money-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_amount'].required = False
        # Tương tự cho đơn nhập
        from catalog.models import Warehouse
        wh = Warehouse.objects.first()
        if wh:
            self.fields['warehouse'].initial = wh
            if Warehouse.objects.count() <= 1:
                self.fields['warehouse'].disabled = True

PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control search-select', 'data-allow-clear': 'false'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input'}),
        'unit_price': forms.TextInput(attrs={'class': 'form-control money-input price-input'}),
    },
    extra=1, can_delete=True
)
