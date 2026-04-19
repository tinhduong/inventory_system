from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('sales/', views.SalesListView.as_view(), name='sales-list'),
    path('sales/create/', views.SalesCreateView.as_view(), name='sales-create'),
    path('sales/<int:pk>/', views.SalesDetailView.as_view(), name='sales-detail'),
    path('sales/<int:pk>/edit/', views.SalesUpdateView.as_view(), name='sales-edit'),
    path('sales/<int:pk>/confirm/', views.confirm_sales_view, name='sales-confirm'),
    path('sales/<int:pk>/delete/', views.delete_sales_order, name='sales-delete'),
    
    path('purchases/', views.PurchaseListView.as_view(), name='purchase-list'),
    path('purchases/create/', views.PurchaseCreateView.as_view(), name='purchase-create'),
    path('purchases/<int:pk>/', views.PurchaseDetailView.as_view(), name='purchase-detail'),
    path('purchases/<int:pk>/edit/', views.PurchaseUpdateView.as_view(), name='purchase-edit'),
    path('purchases/<int:pk>/confirm/', views.confirm_purchase_view, name='purchase-confirm'),
    path('purchases/<int:pk>/delete/', views.delete_purchase_order, name='purchase-delete'),

    path('public/<uuid:token>/', views.customer_public_order_view, name='public-order'),
    path('convert-date/', views.lunar_convert_api, name='convert-date'),
]
