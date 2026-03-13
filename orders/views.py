from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from .models import SalesOrder, PurchaseOrder, OrderStatus
from .forms import SalesOrderForm, SalesOrderLineFormSet, PurchaseOrderForm, PurchaseOrderLineFormSet
from .services.sales_service import confirm_sales_order
from .services.purchase_service import confirm_purchase_order

class SalesListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'orders/sales_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

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

# Purchase views are similar... I'll implement them below
class PurchaseListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'orders/purchase_list.html'
    context_object_name = 'orders'
    ordering = ['-created_at']

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
