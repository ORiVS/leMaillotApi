from rest_framework import serializers
from .models import Vendor
from category.models import Product

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['slug', 'is_approved', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    delivery_fee = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = '__all__'

    def get_delivery_fee(self, obj):
        return obj.vendor.delivery_fee
