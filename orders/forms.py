from django import forms
from django.forms import inlineformset_factory
from .models import SalesOrder, SalesOrderLine, PurchaseOrder, PurchaseOrderLine

class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['code', 'warehouse', 'customer', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
        }

SalesOrderLineFormSet = inlineformset_factory(
    SalesOrder, SalesOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
    },
    extra=1, can_delete=True
)

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['code', 'warehouse', 'supplier', 'order_date']
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
        }

PurchaseOrderLineFormSet = inlineformset_factory(
    PurchaseOrder, PurchaseOrderLine,
    fields=['product', 'quantity', 'unit_price'],
    widgets={
        'product': forms.Select(attrs={'class': 'form-control'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
    },
    extra=1, can_delete=True
)
