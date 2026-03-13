from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Warehouse, Product, StockItem
from .forms import WarehouseForm, ProductForm

class WarehouseListView(LoginRequiredMixin, ListView):
    model = Warehouse
    template_name = 'catalog/warehouse_list.html'
    context_object_name = 'warehouses'

class WarehouseCreateView(LoginRequiredMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'catalog/warehouse_form.html'
    success_url = reverse_lazy('catalog:warehouse-list')

class WarehouseUpdateView(LoginRequiredMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'catalog/warehouse_form.html'
    success_url = reverse_lazy('catalog:warehouse-list')

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product-list')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog:product-list')

class StockListView(LoginRequiredMixin, ListView):
    model = StockItem
    template_name = 'catalog/stock_list.html'
    context_object_name = 'stocks'
    
    def get_queryset(self):
        qs = super().get_queryset()
        warehouse_id = self.request.GET.get('warehouse')
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.all()
        return context
