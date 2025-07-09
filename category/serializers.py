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
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    category_slugs = serializers.SerializerMethodField()
    sizes_display = ProductSizeSerializer(many=True, read_only=True, source='sizes')
    gallery = ProductImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'product_name', 'slug', 'description',
            'price', 'discount_price', 'stock', 'is_available',
            'is_new', 'is_featured', 'image', 'categories', 'category_slugs',
            'sizes', 'sizes_display', 'gallery', 'vendor',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['vendor', 'slug', 'created_at', 'updated_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_category_slugs(self, obj):
        return [cat.slug for cat in obj.categories.all()]

    def create(self, validated_data):
        request = self.context.get('request')

        # 🎯 Traitement des tailles
        raw_sizes = request.data.get('sizes', '[]')
        try:
            sizes_data = json.loads(raw_sizes)
        except json.JSONDecodeError:
            raise serializers.ValidationError({"sizes": "Format JSON invalide"})

        validated_data.pop('sizes', None)

        # ✅ Traitement du champ image
        image_file = request.FILES.get('image')
        if image_file:
            validated_data['image'] = image_file

        # 🛠 Création du produit
        product = Product.objects.create(**validated_data)

        product.categories.set(self.validated_data.get('categories', []))  

        # ✅ Traitement des tailles
        for size_data in sizes_data:
            ProductSize.objects.create(product=product, **size_data)

        # ✅ Traitement des images  multiples (gallery)
        gallery_files = request.FILES.getlist('gallery')
        for file in gallery_files:
            ProductImage.objects.create(product=product, image=file)

        return product