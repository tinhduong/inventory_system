from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine

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
            'warehouse': forms.Select(attrs={'class': 'form-control search-select'}),
            'customer': forms.Select(attrs={'class': 'form-control search-select'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control money-input'}),
        }

SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder, SalesOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control search-select'}),
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
            'warehouse': forms.Select(attrs={'class': 'form-control search-select'}),
            'supplier': forms.Select(attrs={'class': 'form-control search-select'}),
            'paid_amount': forms.TextInput(attrs={'class': 'form-control money-input'}),
        }

PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control search-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input'}),
        'unit_price': forms.TextInput(attrs={'class': 'form-control money-input price-input'}),
    },
    extra=1, can_delete=True
)
