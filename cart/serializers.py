from rest_framework import serializers
from .models import CartItem, Cart
from category.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_products = serializers.SerializerMethodField()
    delivery_estimate = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'created_at',
            'total_products', 'delivery_estimate', 'estimated_total'
        ]
        read_only_fields = ['user', 'created_at']

    def get_total_products(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())

    def get_delivery_estimate(self, obj):
        vendor_ids = set()
        for item in obj.items.all():
            vendor_ids.add(item.product.vendor.id)

        from vendor.models import Vendor
        total_delivery = 0.0
        for vid in vendor_ids:
            try:
                vendor = Vendor.objects.get(id=vid)
                total_delivery += float(vendor.delivery_fee)
            except Vendor.DoesNotExist:
                continue
        return total_delivery

    def get_estimated_total(self, obj):
        return self.get_total_products(obj) + Decimal(self.get_delivery_estimate(obj))
