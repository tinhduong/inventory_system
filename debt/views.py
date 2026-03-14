from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.contrib import messages
from .models import DebtEntry, Settlement, AccountType, DebtStatus
from .forms import SettlementForm, EntryPaymentForm
from accounts.models import Customer
from datetime import date

class DebtOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'debt/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Tính Phải thu (Khách nợ mình)
        rec = DebtEntry.objects.filter(account_type=AccountType.RECEIVABLE)
        total_rec = rec.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        paid_rec = rec.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_receivable'] = total_rec - paid_rec

        # 2. Tính Phải trả (Mình nợ đối tác)
        pay = DebtEntry.objects.filter(account_type=AccountType.PAYABLE)
        total_pay = pay.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        paid_pay = pay.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_payable'] = total_pay - paid_pay

        context['top_customers'] = Customer.objects.all()
        return context

class CustomerDebtDetailView(LoginRequiredMixin, ListView):
    model = DebtEntry
    template_name = 'debt/customer_debt.html'
    context_object_name = 'entries'

    def get_queryset(self):
        # Chỉ lấy các khoản nợ gốc (is_settlement=False), 
        # còn các khoản thanh toán sẽ được lấy qua property payments của từng nợ gốc
        return DebtEntry.objects.filter(
            customer_id=self.kwargs['customer_id'],
            is_settlement=False
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.kwargs['customer_id']
        context['customer'] = Customer.objects.get(pk=customer_id)
        
        entries = DebtEntry.objects.filter(customer_id=customer_id)
        
        # Phải thu của người này
        rec = entries.filter(account_type=AccountType.RECEIVABLE)
        t_rec = rec.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_rec = rec.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['receivable_balance'] = t_rec - p_rec
        
        # Phải trả của người này
        pay = entries.filter(account_type=AccountType.PAYABLE)
        t_pay = pay.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_pay = pay.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['payable_balance'] = t_pay - p_pay
        
        # Net: Dương là mình thu, Âm là mình trả
        context['net_balance'] = context['receivable_balance'] - context['payable_balance']
        
        # Kiểm tra xem có đơn hàng nào chưa xác nhận không (Draft orders)
        from orders.models import SalesOrder, PurchaseOrder, OrderStatus
        context['draft_sales'] = SalesOrder.objects.filter(customer_id=customer_id, status=OrderStatus.DRAFT).count()
        context['draft_purchases'] = PurchaseOrder.objects.filter(supplier_id=customer_id, status=OrderStatus.DRAFT).count()
        
        return context

class EntryPaymentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        entry = get_object_or_404(DebtEntry, pk=pk)
        form = EntryPaymentForm(initial={
            'amount': entry.remaining_amount,
            'payment_date': date.today()
        })
        return render(request, 'debt/entry_payment_form.html', {'form': form, 'entry': entry})

    def post(self, request, pk):
        entry = get_object_or_404(DebtEntry, pk=pk)
        form = EntryPaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            if amount > entry.remaining_amount:
                messages.error(request, "Số tiền thanh toán không được lớn hơn số nợ còn lại.")
                return render(request, 'debt/entry_payment_form.html', {'form': form, 'entry': entry})
            
            # 1. Tạo bản ghi Settlement
            Settlement.objects.create(
                customer=entry.customer,
                account_type=entry.account_type,
                amount_paid=amount,
                payment_date=form.cleaned_data['payment_date'],
                note=form.cleaned_data['note']
            )
            
            # 2. Tạo DebtEntry liên kết
            DebtEntry.objects.create(
                customer=entry.customer,
                account_type=entry.account_type,
                parent_entry=entry,
                amount=amount,
                is_settlement=True,
                note=f"Thanh toán cho đơn: {entry.sales_order.code if entry.sales_order else entry.purchase_order.code}. Nội dung: {form.cleaned_data['note']}"
            )
            
            messages.success(request, f"Đã thanh toán {amount} cho đối tác {entry.customer.name}.")
            return redirect('debt:customer-debt', customer_id=entry.customer.pk)
        
        return render(request, 'debt/entry_payment_form.html', {'form': form, 'entry': entry})

class SettlementCreateView(LoginRequiredMixin, CreateView):
    model = Settlement
    form_class = SettlementForm
    template_name = 'debt/settlement_form.html'
    success_url = '/debt/overview/'

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create a DebtEntry to offset
        DebtEntry.objects.create(
            customer=self.object.customer,
            account_type=self.object.account_type,
            amount=self.object.amount_paid,
            is_settlement=True,
            note=f"Thanh toán/Thu nợ: {self.object.note}"
        )
        return response
