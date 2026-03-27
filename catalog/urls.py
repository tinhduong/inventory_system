from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse-list'),
    path('warehouses/create/', views.WarehouseCreateView.as_view(), name='warehouse-create'),
    path('warehouses/<int:pk>/', views.WarehouseDetailView.as_view(), name='warehouse-detail'),
    path('warehouses/<int:pk>/update/', views.WarehouseUpdateView.as_view(), name='warehouse-update'),
    
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product-create'),
    path('products/export/', views.ExportProductsView.as_view(), name='product-export'),
    path('products/import/', views.ImportProductsView.as_view(), name='product-import'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product-update'),
    
    path('stock/', views.StockListView.as_view(), name='stock-list'),
    path('stock/held-detail/', views.StockHeldDetailView.as_view(), name='stock-held-detail'),
]
