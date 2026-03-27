from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Q, DecimalField, F, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce, Abs, Round
from django.contrib import messages
from .models import DebtEntry, Settlement, AccountType, DebtStatus
from .forms import SettlementForm, EntryPaymentForm
from accounts.models import Customer
from django.http import HttpResponse
from django.utils import timezone
from datetime import date, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

class DebtOverviewView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'debt/overview.html'
    context_object_name = 'customer_list'
    paginate_by = 50

    def test_func(self):
        return self.request.user.role == 'ADMIN'

    def handle_no_permission(self):
        messages.error(self.request, "Bạn không có quyền xem thông tin công nợ.")
        return redirect('dashboard')

    def get_queryset(self):
        # 1. Annotate net balances per customer in the database
        queryset = Customer.objects.annotate(
            t_rec_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.RECEIVABLE, debt_entries__is_settlement=False)), 0, output_field=DecimalField()),
            p_rec_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.RECEIVABLE, debt_entries__is_settlement=True)), 0, output_field=DecimalField()),
            t_pay_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.PAYABLE, debt_entries__is_settlement=False)), 0, output_field=DecimalField()),
            p_pay_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.PAYABLE, debt_entries__is_settlement=True)), 0, output_field=DecimalField()),
        ).annotate(
            balance=Round(ExpressionWrapper(
                (F('t_rec_raw') - F('p_rec_raw')) - (F('t_pay_raw') - F('p_pay_raw')),
                output_field=DecimalField()
            ), 0)
        ).annotate(
            abs_balance=Abs('balance')
        ).order_by('-abs_balance')
        
        # 2. Server-side search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(name__icontains=q)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate system totals from the full UNFILTERED queryset to show system-wide totals in cards
        all_customers_annotated = Customer.objects.annotate(
            t_rec_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.RECEIVABLE, debt_entries__is_settlement=False)), 0, output_field=DecimalField()),
            p_rec_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.RECEIVABLE, debt_entries__is_settlement=True)), 0, output_field=DecimalField()),
            t_pay_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.PAYABLE, debt_entries__is_settlement=False)), 0, output_field=DecimalField()),
            p_pay_raw=Coalesce(Sum('debt_entries__amount', filter=Q(debt_entries__account_type=AccountType.PAYABLE, debt_entries__is_settlement=True)), 0, output_field=DecimalField()),
        ).annotate(
            balance=Round(ExpressionWrapper(
                (F('t_rec_raw') - F('p_rec_raw')) - (F('t_pay_raw') - F('p_pay_raw')),
                output_field=DecimalField()
            ), 0)
        )
        
        totals = all_customers_annotated.aggregate(
            total_rec=Sum(Case(When(balance__gt=0, then=F('balance')), default=0, output_field=DecimalField())),
            total_pay=Sum(Case(When(balance__lt=0, then=Abs(F('balance'))), default=0, output_field=DecimalField())),
        )
        
        context['total_receivable'] = totals['total_rec'] or 0
        context['total_payable'] = totals['total_pay'] or 0
        context['search_query'] = self.request.GET.get('q', '')
        return context

class CustomerDebtDetailView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = DebtEntry
    template_name = 'debt/customer_debt.html'
    context_object_name = 'entries'

    def test_func(self):
        return self.request.user.role == 'ADMIN'

    def handle_no_permission(self):
        messages.error(self.request, "Bạn không có quyền xem thông tin công nợ.")
        return redirect('dashboard')

    def get_queryset(self):
        # Lấy các khoản nợ gốc HOẶC các khoản thanh toán tự do (không có parent)
        qs = DebtEntry.objects.filter(
            Q(customer_id=self.kwargs['customer_id']) & 
            (Q(is_settlement=False) | Q(parent_entry__isnull=True))
        )
        
        # Lọc theo thời gian
        days = self.request.GET.get('days')
        if days and days.isdigit():
            start_date = date.today() - timedelta(days=int(days))
            qs = qs.filter(entry_date__date__gte=start_date)
            
        return qs.order_by('-entry_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.kwargs['customer_id']
        context['customer'] = Customer.objects.get(pk=customer_id)
        
        # 1. Lấy tất cả entries liên quan đến đối tác
        entries = DebtEntry.objects.filter(customer_id=customer_id)
        
        # Áp dụng bộ lọc thời gian cho tính toán tổng hợp
        days = self.request.GET.get('days')
        summary_entries = entries
        if days and days.isdigit():
            start_date = date.today() - timedelta(days=int(days))
            summary_entries = entries.filter(entry_date__date__gte=start_date)

        # Tính toán dư nợ thô để bù trừ
        r_entries = summary_entries.filter(account_type=AccountType.RECEIVABLE)
        t_rec = r_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_rec = r_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        
        p_entries = summary_entries.filter(account_type=AccountType.PAYABLE)
        t_pay = p_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_pay = p_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Số dư tổng (Net) - Làm tròn về số nguyên
        net = round((t_rec - p_rec) - (t_pay - p_pay), 0)
        
        # Bù trừ công nợ (Netting): Chỉ hiện số nợ ở một phía cuối cùng trong Summary Cards
        context['receivable_balance'] = max(0, net)
        context['payable_balance'] = abs(net) if net < 0 else 0
        context['net_balance'] = net
        
        # Draft orders check
        from orders.models import SalesOrder, PurchaseOrder, OrderStatus
        context['draft_sales'] = SalesOrder.objects.filter(customer_id=customer_id, status=OrderStatus.DRAFT).count()
        context['draft_purchases'] = PurchaseOrder.objects.filter(supplier_id=customer_id, status=OrderStatus.DRAFT).count()
        
        context['current_days'] = self.request.GET.get('days', '')
        return context

class ExportDebtHistoryView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'ADMIN'

    def handle_no_permission(self):
        messages.error(self.request, "Bạn không có quyền xuất dữ liệu công nợ.")
        return redirect('dashboard')

    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        
        # Lấy toàn bộ lịch sử giao dịch (Sổ cái) để đảm bảo SUM(Nợ) trong Excel = Số dư thực tế
        qs = DebtEntry.objects.filter(customer=customer).select_related('sales_order', 'purchase_order')
        
        days = request.GET.get('days')
        time_label = "Tat ca"
        if days and days.isdigit():
            start_date = date.today() - timedelta(days=int(days))
            qs = qs.filter(entry_date__date__gte=start_date)
            time_label = f"Trong {days} ngay"

        qs = qs.order_by('-entry_date', '-created_at')

        # Tạo workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Lich su cong no"

        # Định dạng header theo yêu cầu mới
        headers = ["Ngày ghi", "Nội dung / Chứng từ", "Mã đơn", "Giá trị đơn mua", "Giá trị đơn bán", "Đã thanh toán", "Khoản phải thu", "Khoản phải chi"]
        ws.append(headers)
        
        header_fill = PatternFill(start_color="3498db", end_color="3498db", fill_type="solid")
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Thêm dữ liệu (Logic Nhật ký giao dịch để SUM cột nợ chính xác trong Excel)
        for entry in qs:
            po_val = 0
            so_val = 0
            paid = 0
            rem_rec = 0
            rem_pay = 0

            if entry.is_settlement:
                # Đây là khoản thanh toán / thu nợ (Làm giảm nợ -> Ghi âm số tiền vào cột nợ)
                paid = float(entry.amount)
                if entry.account_type == AccountType.RECEIVABLE:
                    rem_rec = -paid
                else:
                    rem_pay = -paid
            else:
                # Đây là hóa đơn gốc (Làm tăng nợ -> Ghi dương toàn bộ giá trị đơn)
                if entry.account_type == AccountType.RECEIVABLE: # Bán hàng
                    so_val = float(entry.amount)
                    rem_rec = so_val
                else: # Nhập hàng
                    po_val = float(entry.amount)
                    rem_pay = po_val

            note_with_type = entry.note or ""
            if entry.is_settlement:
                type_label = "[Thu]" if entry.account_type == AccountType.RECEIVABLE else "[Chi]"
                note_with_type = f"{type_label} {note_with_type}"

            row = [
                entry.entry_date.strftime("%d/%m/%Y %H:%M") if entry.entry_date else entry.created_at.strftime("%d/%m/%Y %H:%M"),
                note_with_type,
                entry.sales_order.code if entry.sales_order else (entry.purchase_order.code if entry.purchase_order else ""),
                po_val,
                so_val,
                paid,
                rem_rec,
                rem_pay
            ]
            ws.append(row)

        # Điều chỉnh độ rộng cột
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            ws.column_dimensions[column].width = max_length + 2

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="CongNo_{customer.name}_{time_label}.xlsx"'
        wb.save(response)
        return response

class EntryPaymentView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role == 'ADMIN'
    
    def handle_no_permission(self):
        messages.error(self.request, "Bạn không có quyền thực hiện thanh toán công nợ.")
        return redirect('dashboard')

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
                note=f"Thanh toán cho đơn: {entry.sales_order.code if entry.sales_order else entry.purchase_order.code}. Nội dung: {form.cleaned_data['note']}",
                entry_date=form.cleaned_data['payment_date']
            )
            
            messages.success(request, f"Đã thanh toán {amount} cho đối tác {entry.customer.name}.")
            return redirect('debt:customer-debt', customer_id=entry.customer.pk)
        
        return render(request, 'debt/entry_payment_form.html', {'form': form, 'entry': entry})

class SettlementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Settlement
    form_class = SettlementForm
    template_name = 'debt/settlement_form.html'
    success_url = '/debt/overview/'

    def test_func(self):
        return self.request.user.role == 'ADMIN'
    
    def handle_no_permission(self):
        messages.error(self.request, "Bạn không có quyền quyết toán công nợ.")
        return redirect('dashboard')

    def get_initial(self):
        initial = super().get_initial()
        customer_id = self.request.GET.get('customer')
        account_type = self.request.GET.get('account_type')
        if customer_id:
            initial['customer'] = customer_id
        if account_type:
            initial['account_type'] = account_type
        initial['payment_date'] = date.today()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.request.GET.get('customer')
        if customer_id:
            customer = get_object_or_404(Customer, pk=customer_id)
            context['current_customer'] = customer
            
            # Calculate debts
            entries = DebtEntry.objects.filter(customer=customer)
            # Receivable
            tr = entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pr = entries.filter(account_type=AccountType.RECEIVABLE, is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            # Payable
            tp = entries.filter(account_type=AccountType.PAYABLE, is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pp = entries.filter(account_type=AccountType.PAYABLE, is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Netting logic same as detail view
            net = round((tr - pr) - (tp - pp), 0)
            context['net_balance'] = net
            context['abs_net_balance'] = abs(net)
        return context

    def get_success_url(self):
        return reverse_lazy('debt:settlement-success')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create a DebtEntry to offset
        DebtEntry.objects.create(
            customer=self.object.customer,
            account_type=self.object.account_type,
            amount=self.object.amount_paid,
            is_settlement=True,
            note=f"Thanh toán/Thu nợ: {self.object.note}",
            entry_date=self.object.payment_date
        )
        return response

class SettlementSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "debt/settlement_success.html"
