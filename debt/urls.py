from django.urls import path
from . import views

app_name = 'debt'

urlpatterns = [
    path('overview/', views.DebtOverviewView.as_view(), name='overview'),
    path('customer/<int:customer_id>/', views.CustomerDebtDetailView.as_view(), name='customer-debt'),
    path('customer/<int:customer_id>/export/', views.ExportDebtHistoryView.as_view(), name='export-debt-history'),
    path('settlement/create/', views.SettlementCreateView.as_view(), name='settlement-create'),
    path('settlement/success/', views.SettlementSuccessView.as_view(), name='settlement-success'),
    path('entry/<int:pk>/pay/', views.EntryPaymentView.as_view(), name='entry-payment'),
]
