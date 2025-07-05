from rest_framework import serializers
from .models import CartItem, Cart
from category.models import Product
from decimal import Decimal

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_image = serializers.SerializerMethodField()
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    size = serializers.CharField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_image', 'product_price', 'quantity', 'size']

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.image:
            return request.build_absolute_uri(obj.product.image.url)
        return None

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_products = serializers.SerializerMethodField()
    delivery_estimate = serializers.SerializerMethodField()
    estimated_total = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()  # 👈 AJOUT ICI

    class Meta:
        model = Cart
        fields = [
            'id', 'user', 'items', 'created_at',
            'total_products', 'delivery_estimate', 'estimated_total',
            'total_items'  # 👈 AJOUT ICI
        ]
        read_only_fields = ['user', 'created_at']

    def get_total_products(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())

    def get_delivery_estimate(self, obj):
        vendor_ids = {item.product.vendor.id for item in obj.items.all()}

        from vendor.models import Vendor
        total_delivery = Decimal("0.0")
        for vid in vendor_ids:
            try:
                vendor = Vendor.objects.get(id=vid)
                total_delivery += vendor.delivery_fee or Decimal("0.0")
            except Vendor.DoesNotExist:
                continue
        return total_delivery

    def get_estimated_total(self, obj):
        return self.get_total_products(obj) + Decimal(self.get_delivery_estimate(obj))

    def get_total_items(self, obj):  # 👈 AJOUT ICI
        return sum(item.quantity for item in obj.items.all())
