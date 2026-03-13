from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Customer, User
from .forms import CustomerForm, UserForm

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'ADMIN'

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'accounts/customer_list.html'
    context_object_name = 'customers'

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'accounts/customer_form.html'
    success_url = reverse_lazy('accounts:customer-list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'accounts/customer_form.html'
    success_url = reverse_lazy('accounts:customer-list')

# User Management
class UserListView(SuperuserRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

class UserCreateView(SuperuserRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user-list')

class UserUpdateView(SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user-list')


class UserDeleteView(SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user-list')
