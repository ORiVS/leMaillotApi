from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from accounts.permissions import IsVendor
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

class BaseVendorProtectedView:
    def get_vendor_or_403(self):
        try:
            return self.request.user.vendor
        except Exception:
            raise PermissionDenied("Aucun profil vendeur associé à ce compte.")


class CategoryListCreateAPIView(BaseVendorProtectedView, generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.get_vendor_or_403()
        return Category.objects.filter(vendor=vendor)

    def perform_create(self, serializer):
        vendor = self.get_vendor_or_403()
        serializer.save(vendor=vendor)


class CategoryRetrieveUpdateDestroyAPIView(BaseVendorProtectedView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.get_vendor_or_403()
        return Category.objects.filter(vendor=vendor)


class ProductListCreateAPIView(BaseVendorProtectedView, generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.get_vendor_or_403()
        return Product.objects.filter(vendor=vendor)

    def perform_create(self, serializer):
        vendor = self.get_vendor_or_403()
        serializer.save(vendor=vendor)


class ProductRetrieveUpdateDestroyAPIView(BaseVendorProtectedView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        vendor = self.get_vendor_or_403()
        return Product.objects.filter(vendor=vendor)
