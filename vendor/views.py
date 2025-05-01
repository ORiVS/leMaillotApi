from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from category.models import Product
from category.serializers import ProductSerializer
from vendor.models import Vendor
from vendor.serializers import VendorSerializer


class VendorDetailAPIView(generics.RetrieveAPIView):
    queryset = Vendor.objects.filter(is_approved=True)
    serializer_class = VendorSerializer
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        vendor = self.get_object()
        products = Product.objects.filter(vendor=vendor, is_available=True)
        product_data = ProductSerializer(products, many=True, context={'request': request}).data
        vendor_data = self.get_serializer(vendor).data
        vendor_data['products'] = product_data
        return Response(vendor_data)

class VendorListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vendor.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, user_profile=self.request.user.userprofile)


class VendorRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Vendor.objects.filter(user=self.request.user)