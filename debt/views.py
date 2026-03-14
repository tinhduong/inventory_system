from django.shortcuts import render, redirect
from django.views.generic import ListView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from .models import DebtEntry, Settlement, AccountType
from .forms import SettlementForm
from accounts.models import Customer

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
        return DebtEntry.objects.filter(customer_id=self.kwargs['customer_id']).order_by('-created_at')

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
        
        return context

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
