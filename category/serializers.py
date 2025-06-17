from rest_framework import serializers
import json
from .models import Category, Product, ProductImage, ProductSize


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'slug', 'description', 'image']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_main']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['size', 'stock']

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    sizes = serializers.CharField(write_only=True)
    sizes_display = ProductSizeSerializer(many=True, read_only=True, source='sizes')
    gallery = ProductImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()  # ✅ override champ image

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['vendor', 'slug', 'created_at', 'updated_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None

    def create(self, validated_data):
        request = self.context.get('request')

        raw_sizes = request.data.get('sizes', '[]')
        try:
            sizes_data = json.loads(raw_sizes)
        except json.JSONDecodeError:
            raise serializers.ValidationError({"sizes": "Format JSON invalide"})

        validated_data.pop('sizes', None)
        product = Product.objects.create(**validated_data)

        for size_data in sizes_data:
            ProductSize.objects.create(product=product, **size_data)

        return product
