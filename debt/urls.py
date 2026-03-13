from django.urls import path
from . import views

app_name = 'debt'

urlpatterns = [
    path('overview/', views.DebtOverviewView.as_view(), name='overview'),
    path('customer/<int:customer_id>/', views.CustomerDebtDetailView.as_view(), name='customer-debt'),
    path('settlement/create/', views.SettlementCreateView.as_view(), name='settlement-create'),
]
