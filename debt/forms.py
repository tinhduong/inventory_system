from django import forms
from django.db.models import Sum, Q, DecimalField
from django.db.models.functions import Coalesce
from .models import Settlement, DebtEntry, AccountType

class SettlementForm(forms.ModelForm):
    class Meta:
        model = Settlement
        fields = ['customer', 'account_type', 'amount_paid', 'payment_date', 'note']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.TextInput(attrs={'class': 'form-control money-input', 'autocomplete': 'off'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable customer and account_type if they are already set (from initial/GET params)
        if self.initial.get('customer'):
            self.fields['customer'].disabled = True
        if self.initial.get('account_type'):
            self.fields['account_type'].disabled = True

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        
        # In Django, disabled fields do NOT appear in cleaned_data if not submitted.
        # But we need the customer to validate. 
        # We can get it from initial or from the instance if it's already there.
        customer_id = self.cleaned_data.get('customer') or self.initial.get('customer')
        
        if customer_id and amount is not None:
            # Handle case where customer might be an ID or an object
            from accounts.models import Customer
            if isinstance(customer_id, Customer):
                customer = customer_id
            else:
                customer = Customer.objects.get(pk=customer_id)
                
            entries = DebtEntry.objects.filter(customer=customer)
            tr = entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pr = entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            tp = entries.filter(account_type=AccountType.PAYABLE, is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pp = entries.filter(account_type=AccountType.PAYABLE, is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            
            net_balance = round((tr - pr) - (tp - pp), 0)
            abs_balance = abs(net_balance)
            
            if abs_balance <= 0:
                raise forms.ValidationError("Đối tác hiện không còn dư nợ. Không thể tạo phiếu quyết toán.")
            
            if amount > abs_balance:
                from django.contrib.humanize.templatetags.humanize import intcomma
                raise forms.ValidationError(f"Số tiền quyết toán ({intcomma(int(amount))} đ) không được lớn hơn dư nợ hiện tại ({intcomma(int(abs_balance))} đ).")
            
            if amount <= 0:
                raise forms.ValidationError("Số tiền quyết toán phải lớn hơn 0.")
        
        return amount

class EntryPaymentForm(forms.Form):
    amount = forms.DecimalField(max_digits=15, decimal_places=2, label="Số tiền thanh toán", widget=forms.TextInput(attrs={'class': 'form-control money-input'}))
    payment_date = forms.DateField(label="Ngày thanh toán", widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    note = forms.CharField(label="Ghi chú", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class OldDebtForm(forms.ModelForm):
    class Meta:
        model = DebtEntry
        fields = ['customer', 'account_type', 'amount', 'entry_date', 'note']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.TextInput(attrs={'class': 'form-control money-input', 'autocomplete': 'off'}),
            'entry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'amount': 'Số dư công nợ cũ',
            'entry_date': 'Ngày hạch toán',
            'note': 'Ghi chú',
            'account_type': 'Loại công nợ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.initial.get('customer'):
            self.fields['customer'].disabled = True
