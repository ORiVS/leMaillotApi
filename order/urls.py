from django.urls import path
from .views import OrderCreateAPIView, OrderListAPIView, VendorOrderListAPIView, VendorOrderDetailAPIView, \
    AdminOrderListAPIView, CustomerOrderDetailAPIView, ExportOrderPDFAPIView

urlpatterns = [
    path('', OrderListAPIView.as_view(), name='order-list'),
    path('create/', OrderCreateAPIView.as_view(), name='order-create'),
    path('vendor/', VendorOrderListAPIView.as_view(), name='vendor-orders'),
    path('vendor/<int:pk>/', VendorOrderDetailAPIView.as_view(), name='vendor-order-detail'),
    path('admin/', AdminOrderListAPIView.as_view(), name='admin-orders'),
    path('<int:pk>/', CustomerOrderDetailAPIView.as_view(), name='customer-order-detail'),
    path('<int:pk>/export/', ExportOrderPDFAPIView.as_view(), name='export-order-pdf'),

]
