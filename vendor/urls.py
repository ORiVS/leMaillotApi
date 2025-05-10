from django.urls import path, include
from .import views
from .views import VendorDetailAPIView, VendorListCreateAPIView, VendorRetrieveUpdateDestroyAPIView

urlpatterns = [

    path('vendors/<slug:slug>/', VendorDetailAPIView.as_view(), name='vendor-detail'),
    path('vendors/', VendorListCreateAPIView.as_view(), name='vendor-list-create'),
    path('vendors/<int:pk>/', VendorRetrieveUpdateDestroyAPIView.as_view(), name='vendor-detail'),
    path('vendors/public/<slug:slug>/', VendorDetailAPIView.as_view(), name='vendor-public-detail'),
]