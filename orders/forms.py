from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine

def generate_order_code(prefix, model_class):
    today_str = timezone.now().strftime('%y%m%d')
    # Tìm mã đơn hàng cao nhất trong ngày
    last_order = model_class.objects.filter(code__startswith=f"{prefix}{today_str}").order_by('-code').first()
    
    if last_order:
        last_num = int(last_order.code.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
        
    return f"{prefix}{today_str}-{new_num:03d}"

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['warehouse', 'customer', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
        }

SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder, SalesOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'unit_price': forms.TextInput(attrs={'class': 'form-control money-input'}),
    },
    extra=1, can_delete=True
)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['warehouse', 'supplier', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'unit_price': forms.TextInput(attrs={'class': 'form-control money-input'}),
    },
    extra=1, can_delete=True
)
