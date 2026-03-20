from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import SalesOrder, PurchaseOrder, OrderStatus
from .forms import SalesOrderForm, SalesOrderLineFormSet, PurchaseOrderForm, PurchaseOrderLineFormSet
from .services.sales_service import confirm_sales_order
from .services.purchase_service import confirm_purchase_order
from accounts.models import Customer

def get_period_filter(period):
    today = timezone.now().date()
    if period == 'today':
        return today, today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif period == '7d':
        return today - timedelta(days=7), today
    elif period == '1m':
        return today - timedelta(days=30), today
    elif period == '3m':
        return today - timedelta(days=90), today
    elif period == '6m':
        return today - timedelta(days=180), today
    elif period == '1y':
        return today - timedelta(days=365), today
    return None, None

class SalesListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'orders/sales_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 1. Filter by Payment Status (Unpaid)
        payment_status = self.request.GET.get('payment_status')
        if payment_status == 'unpaid':
            from django.db.models import Sum, Q, F
            from debt.models import DebtEntry
            queryset = queryset.filter(status=OrderStatus.CONFIRMED)
            debt_qs = DebtEntry.objects.filter(sales_order__isnull=False, is_settlement=False)
            debt_qs = debt_qs.annotate(total_paid=Sum('payments__amount'))
            unpaid_debt_ids = debt_qs.filter(
                Q(total_paid__isnull=True) | Q(total_paid__lt=F('amount'))
            ).values_list('sales_order_id', flat=True)
            queryset = queryset.filter(id__in=unpaid_debt_ids)

        # 2. Filter by Period
        period = self.request.GET.get('period')
        start_date, end_date = get_period_filter(period)
        if start_date and end_date:
            if start_date == end_date:
                queryset = queryset.filter(order_date=start_date)
            else:
                queryset = queryset.filter(order_date__range=[start_date, end_date])

        # 3. Filter by Customer
        customer_id = self.request.GET.get('customer')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_status'] = self.request.GET.get('payment_status', 'all')
        context['current_period'] = self.request.GET.get('period', 'all')
        context['current_customer'] = self.request.GET.get('customer', '')
        context['customers'] = Customer.objects.all().order_by('name')
        return context

class SalesDetailView(LoginRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'orders/sales_detail.html'
    context_object_name = 'order'

class SalesCreateView(LoginRequiredMixin, CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'orders/sales_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['lines'] = SalesOrderLineFormSet(self.request.POST)
        else:
            data['lines'] = SalesOrderLineFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            form.instance.employee = self.request.user
            self.object = form.save()
            lines.instance = self.object
            lines.save()
            # Calculate total amount
            self.object.total_amount = sum(line.line_total for line in self.object.lines.all())
            self.object.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('orders:sales-detail', kwargs={'pk': self.object.pk})

def confirm_sales_view(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    try:
        confirm_sales_order(order)
        messages.success(request, f"Đơn hàng {order.code} đã được xác nhận và trừ tồn kho.")
    except Exception as e:
        messages.error(request, f"Lỗi khi xác nhận: {str(e)}")
    return redirect('orders:sales-detail', pk=pk)

class PurchaseListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'orders/purchase_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 1. Filter by Payment Status (Unpaid)
        payment_status = self.request.GET.get('payment_status')
        if payment_status == 'unpaid':
            from django.db.models import Sum, Q, F
            from debt.models import DebtEntry
            queryset = queryset.filter(status=OrderStatus.CONFIRMED)
            debt_qs = DebtEntry.objects.filter(purchase_order__isnull=False, is_settlement=False)
            debt_qs = debt_qs.annotate(total_paid=Sum('payments__amount'))
            unpaid_debt_ids = debt_qs.filter(
                Q(total_paid__isnull=True) | Q(total_paid__lt=F('amount'))
            ).values_list('purchase_order_id', flat=True)
            queryset = queryset.filter(id__in=unpaid_debt_ids)

        # 2. Filter by Period
        period = self.request.GET.get('period')
        start_date, end_date = get_period_filter(period)
        if start_date and end_date:
            if start_date == end_date:
                queryset = queryset.filter(order_date=start_date)
            else:
                queryset = queryset.filter(order_date__range=[start_date, end_date])

        # 3. Filter by Supplier
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_status'] = self.request.GET.get('payment_status', 'all')
        context['current_period'] = self.request.GET.get('period', 'all')
        context['current_supplier'] = self.request.GET.get('supplier', '')
        context['suppliers'] = Customer.objects.all().order_by('name')
        return context

class PurchaseDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'orders/purchase_detail.html'
    context_object_name = 'order'

class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'orders/purchase_form.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['lines'] = PurchaseOrderLineFormSet(self.request.POST)
        else:
            data['lines'] = PurchaseOrderLineFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        lines = context['lines']
        if lines.is_valid():
            form.instance.employee = self.request.user
            self.object = form.save()
            lines.instance = self.object
            lines.save()
            self.object.total_amount = sum(line.line_total for line in self.object.lines.all())
            self.object.save()
            return redirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse('orders:purchase-detail', kwargs={'pk': self.object.pk})

def confirm_purchase_view(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    try:
        confirm_purchase_order(order)
        messages.success(request, f"Đơn nhập {order.code} đã được xác nhận và cộng tồn kho.")
    except Exception as e:
        messages.error(request, f"Lỗi khi xác nhận: {str(e)}")
    return redirect('orders:purchase-detail', pk=pk)

def delete_sales_order(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    if request.user.role != 'ADMIN':
        messages.error(request, "Chỉ Admin mới có quyền xóa đơn hàng.")
        return redirect('orders:sales-detail', pk=pk)
    
    if order.status != OrderStatus.DRAFT:
        messages.error(request, "Chỉ có thể xóa đơn hàng ở trạng thái Nháp.")
        return redirect('orders:sales-detail', pk=pk)
    
    code = order.code
    order.delete()
    messages.success(request, f"Đã xóa đơn hàng {code} thành công.")
    return redirect('orders:sales-list')

def delete_purchase_order(request, pk):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    if request.user.role != 'ADMIN':
        messages.error(request, "Chỉ Admin mới có quyền xóa đơn nhập.")
        return redirect('orders:purchase-detail', pk=pk)
    
    if order.status != OrderStatus.DRAFT:
        messages.error(request, "Chỉ có thể xóa đơn nhập ở trạng thái Nháp.")
        return redirect('orders:purchase-detail', pk=pk)
    
    code = order.code
    order.delete()
    messages.success(request, f"Đã xóa đơn nhập {code} thành công.")
    return redirect('orders:purchase-list')

def customer_public_order_view(request, token):
    # Try SalesOrder
    order = SalesOrder.objects.filter(public_token=token).first()
    if order:
        return render(request, 'orders/public_order.html', {'order': order, 'type': 'sales'})
    # Try PurchaseOrder
    order = PurchaseOrder.objects.filter(public_token=token).first()
    if order:
        return render(request, 'orders/public_order.html', {'order': order, 'type': 'purchase'})
    return render(request, '404.html', status=404)
