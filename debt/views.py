from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, TemplateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.contrib import messages
from .models import DebtEntry, Settlement, AccountType, DebtStatus
from .forms import SettlementForm, EntryPaymentForm
from accounts.models import Customer
from django.http import HttpResponse
from datetime import date, timedelta
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

class DebtOverviewView(LoginRequiredMixin, TemplateView):
    template_name = 'debt/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Tính Phải thu (Tổng hệ thống)
        rec = DebtEntry.objects.filter(account_type=AccountType.RECEIVABLE)
        total_rec = rec.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        paid_rec = rec.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_receivable'] = total_rec - paid_rec

        # 2. Tính Phải trả (Tổng hệ thống)
        pay = DebtEntry.objects.filter(account_type=AccountType.PAYABLE)
        total_pay = pay.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        paid_pay = pay.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_payable'] = total_pay - paid_pay

        # 3. Tính toán nợ cho từng đối tác để tìm TOP và hỗ trợ search
        customers = Customer.objects.all()
        customer_list = []
        for c in customers:
            entries = DebtEntry.objects.filter(customer=c)
            # Thu
            r = entries.filter(account_type=AccountType.RECEIVABLE)
            tr = r.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pr = r.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            # Trả
            p = entries.filter(account_type=AccountType.PAYABLE)
            tp = p.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
            pp = p.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
            
            balance = (tr - pr) - (tp - pp)
            customer_list.append({
                'obj': c,
                'balance': balance,
                'abs_balance': abs(balance)
            })
        
        # Sắp xếp theo dư nợ tuyệt đối giảm dần
        customer_list.sort(key=lambda x: x['abs_balance'], reverse=True)
        context['customer_list'] = customer_list
        return context

class CustomerDebtDetailView(LoginRequiredMixin, ListView):
    model = DebtEntry
    template_name = 'debt/customer_debt.html'
    context_object_name = 'entries'

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
            qs = qs.filter(created_at__date__gte=start_date)
            
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer_id = self.kwargs['customer_id']
        context['customer'] = Customer.objects.get(pk=customer_id)
        
        entries = DebtEntry.objects.filter(customer_id=customer_id)
        
        # 1. Tính Phải thu (Khách nợ mình)
        rec_entries = entries.filter(account_type=AccountType.RECEIVABLE)
        t_rec = rec_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_rec = rec_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        # Số tiền khách thực sự còn nợ (Nếu < 0 là khách trả dư)
        context['receivable_balance'] = t_rec - p_rec
        
        # 2. Tính Phải trả (Mình nợ họ)
        pay_entries = entries.filter(account_type=AccountType.PAYABLE)
        t_pay = pay_entries.filter(is_settlement=False).aggregate(Sum('amount'))['amount__sum'] or 0
        p_pay = pay_entries.filter(is_settlement=True).aggregate(Sum('amount'))['amount__sum'] or 0
        # Số tiền mình thực sự còn nợ (Nếu < 0 là mình trả dư)
        context['payable_balance'] = t_pay - p_pay
        
        # 3. Số dư tổng cuối cùng
        # Nếu > 0: Tổng cộng mình đang cần thu về từ người này
        # Nếu < 0: Tổng cộng mình đang cần trả cho người này
        context['net_balance'] = context['receivable_balance'] - context['payable_balance']
        
        # Draft orders check
        from orders.models import SalesOrder, PurchaseOrder, OrderStatus
        context['draft_sales'] = SalesOrder.objects.filter(customer_id=customer_id, status=OrderStatus.DRAFT).count()
        context['draft_purchases'] = PurchaseOrder.objects.filter(supplier_id=customer_id, status=OrderStatus.DRAFT).count()
        
        context['current_days'] = self.request.GET.get('days', '')
        return context

class ExportDebtHistoryView(LoginRequiredMixin, View):
    def get(self, request, customer_id):
        customer = get_object_or_404(Customer, pk=customer_id)
        
        # Áp dụng logic filter tương tự get_queryset
        qs = DebtEntry.objects.filter(
            Q(customer=customer) & 
            (Q(is_settlement=False) | Q(parent_entry__isnull=True))
        )
        
        days = request.GET.get('days')
        time_label = "Tat ca"
        if days and days.isdigit():
            start_date = date.today() - timedelta(days=int(days))
            qs = qs.filter(created_at__date__gte=start_date)
            time_label = f"Trong {days} ngay"

        qs = qs.order_by('-created_at')

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

        # Thêm dữ liệu
        for entry in qs:
            po_val = 0
            so_val = 0
            paid = 0
            rem_rec = 0
            rem_pay = 0

            if entry.is_settlement:
                # Phiếu thu/chi tự do
                paid = float(entry.amount)
            else:
                # Đơn hàng
                if entry.account_type == AccountType.RECEIVABLE: # Bán hàng
                    so_val = float(entry.amount)
                    paid = float(entry.paid_amount)
                    rem_rec = float(entry.remaining_amount)
                else: # Nhập hàng
                    po_val = float(entry.amount)
                    paid = float(entry.paid_amount)
                    rem_pay = float(entry.remaining_amount)

            row = [
                entry.created_at.strftime("%d/%m/%Y %H:%M"),
                entry.note,
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
