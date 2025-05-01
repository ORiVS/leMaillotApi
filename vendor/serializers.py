from rest_framework import serializers
from .models import Vendor

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['vendor_name', 'slug', 'is_approved', 'created_at']
        read_only_fields = ['slug', 'is_approved', 'created_at']

