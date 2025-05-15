from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from category.models import Product
from category.serializers import ProductSerializer
from vendor.models import Vendor
from vendor.serializers import VendorSerializer

from rest_framework.views import APIView
from rest_framework import status
from .utils import haversine

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

class NearbyVendorsAPIView(APIView):
    def get(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 10))  # km
        except (TypeError, ValueError):
            return Response({"error": "Paramètres lat, lng et radius requis."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for vendor in Vendor.objects.filter(is_approved=True):
            if vendor.latitude is not None and vendor.longitude is not None:
                distance = haversine(lat, lng, vendor.latitude, vendor.longitude)
                if distance <= radius:
                    data = VendorSerializer(vendor).data
                    data['distance_km'] = round(distance, 2)
                    results.append(data)

        return Response(sorted(results, key=lambda x: x['distance_km']))

class NearbyProductsAPIView(APIView):
    def get(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
            radius = float(request.query_params.get('radius', 10))  # rayon en km
        except (TypeError, ValueError):
            return Response({"error": "Paramètres lat, lng et radius requis."}, status=status.HTTP_400_BAD_REQUEST)

        # Filtrer les vendeurs proches
        nearby_vendor_ids = []
        for vendor in Vendor.objects.filter(is_approved=True):
            if vendor.latitude is not None and vendor.longitude is not None:
                distance = haversine(lat, lng, vendor.latitude, vendor.longitude)
                if distance <= radius:
                    nearby_vendor_ids.append(vendor.id)

        # Récupérer les produits de ces vendeurs
        products = Product.objects.filter(vendor__id__in=nearby_vendor_ids)
        serialized = ProductSerializer(products, many=True)

        return Response(serialized.data, status=status.HTTP_200_OK)