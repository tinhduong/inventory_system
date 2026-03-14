from django import forms
from .models import Settlement

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = ['customer', 'account_type', 'amount_paid', 'payment_date', 'note']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EntryPaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=15, decimal_places=2, label="Số tiền thanh toán", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    payment_date = forms.DateField(label="Ngày thanh toán", widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    note = forms.CharField(label="Ghi chú", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
