from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from accounts.permissions import IsVendor
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer

# 🔓 Vue publique pour afficher toutes les catégories
class PublicCategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by('category_name')
    serializer_class = CategorySerializer
    permission_classes = []

class BaseVendorProtectedView:
    def get_vendor_or_403(self):
        try:
            return self.request.user.vendor
        except Exception:
            raise PermissionDenied("Aucun profil vendeur associé à ce compte.")

# 🛒 CRUD des produits par les vendeurs
class ProductListCreateAPIView(BaseVendorProtectedView, generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.get_vendor_or_403())

    def perform_create(self, serializer):
        vendor = self.get_vendor_or_403()
        serializer.save(vendor=vendor)


class ProductRetrieveUpdateDestroyAPIView(BaseVendorProtectedView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.get_vendor_or_403())

class PublicProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = []  # Accès libre

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)

        # 🔍 Filtres GET
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        featured = self.request.query_params.get('featured')
        if featured == "true":
            queryset = queryset.filter(is_featured=True)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__category_name__icontains=search)
            )

        return queryset.order_by('-created_at')