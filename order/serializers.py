from django.http import HttpResponse
from django.http import FileResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, TableStyle, Table
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import Order, OrderItem, OrderStatusHistory
from category.models import Product
from decimal import Decimal
from .utils.invoice_generator import generate_invoice


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    vendor_name = serializers.CharField(source='product.vendor.vendor_name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'vendor_name', 'quantity', 'price']
        read_only_fields = ['price']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_city = serializers.CharField(required=False, allow_blank=True)
    delivery_postal_code = serializers.CharField(required=False, allow_blank=True)
    delivery_country = serializers.CharField(required=False, allow_blank=True)
    delivery_latitude = serializers.FloatField(required=False)
    delivery_longitude = serializers.FloatField(required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'delivery_method',
            'delivery_address', 'delivery_city', 'delivery_postal_code', 'delivery_country',
            'delivery_latitude', 'delivery_longitude',
            'delivery_cost', 'total_price', 'created_at', 'items'
        ]
        read_only_fields = ['customer', 'status', 'delivery_cost', 'total_price', 'created_at']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("La commande doit contenir au moins un produit.")
        return items

    def validate(self, data):
        user = self.context['request'].user
        profile = getattr(user, 'userprofile', None)
        delivery_method = data.get('delivery_method', 'pickup')

        # Fallback depuis le profil si champ manquant
        data['delivery_address'] = data.get('delivery_address') or profile.address_line_1
        data['delivery_city'] = data.get('delivery_city') or profile.city
        data['delivery_postal_code'] = data.get('delivery_postal_code') or profile.pin_code
        data['delivery_country'] = data.get('delivery_country') or profile.country
        data['delivery_latitude'] = data.get('delivery_latitude') or profile.latitude
        data['delivery_longitude'] = data.get('delivery_longitude') or profile.longitude

        # ✅ Vérification dynamique selon le mode de livraison
        if delivery_method == "delivery" and not data.get('delivery_address'):
            raise serializers.ValidationError("L'adresse de livraison est obligatoire pour une livraison à domicile.")

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = self.context['request'].user

        # Extraire les données d'adresse
        delivery_address = validated_data.get('delivery_address')
        delivery_city = validated_data.get('delivery_city')
        delivery_postal_code = validated_data.get('delivery_postal_code')
        delivery_country = validated_data.get('delivery_country')
        delivery_latitude = validated_data.get('delivery_latitude')
        delivery_longitude = validated_data.get('delivery_longitude')
        delivery_method = validated_data.get('delivery_method')

        delivery_cost = 0.0
        total_price = 0
        vendor_ids = set()

        # Création de la commande
        order = Order.objects.create(
            customer=customer,
            delivery_method=delivery_method,
            delivery_address=delivery_address,
            delivery_city=delivery_city,
            delivery_postal_code=delivery_postal_code,
            delivery_country=delivery_country,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            delivery_cost=0.0,
            total_price=0
        )

        for item in items_data:
            product_id = item.get('product')
            quantity = item.get('quantity', 1)
            product = Product.objects.get(id=product_id, is_available=True)

            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour le produit '{product.product_name}' (stock actuel : {product.stock})"
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price
            )

            total_price += product.price * quantity
            product.stock -= quantity
            product.save()

            vendor_ids.add(product.vendor.id)

        # Frais de livraison par vendeur si applicable
        if delivery_method == 'delivery':
            from vendor.models import Vendor
            for vid in vendor_ids:
                vendor = Vendor.objects.get(id=vid)
                delivery_cost += float(vendor.delivery_fee)

        order.delivery_cost = delivery_cost
        order.total_price = total_price + Decimal(delivery_cost)
        order.save()

        return order


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)

    class Meta:
        model = OrderStatusHistory
        fields = ['previous_status', 'new_status', 'changed_by_email', 'changed_at']

class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    order_number = serializers.CharField(read_only=True)
    delivery_address = serializers.CharField()
    delivery_city = serializers.CharField()
    delivery_postal_code = serializers.CharField()
    delivery_country = serializers.CharField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer_email', 'total_price', 'delivery_cost', 'delivery_method',
            'status', 'created_at', 'items', 'status_history', 'order_number', 'delivery_address', 'delivery_city', 'delivery_postal_code', 'delivery_country',
        'delivery_latitude', 'delivery_longitude'
        ]

class VendorOrderDetailSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    customer_email = serializers.EmailField(source='customer.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'customer_email',
            'delivery_method',
            'delivery_cost',  # total global, ou tu peux le cacher
            'status',
            'created_at',
            'items',
            'total_price',  # total partiel (produits du vendeur)
        ]

    def get_items(self, obj):
        """Retourne uniquement les items du vendeur connecté"""
        user = self.context['request'].user
        if not hasattr(user, 'vendor'):
            return []

        items = obj.items.filter(product__vendor=user.vendor)
        return OrderItemSerializer(items, many=True).data

    def get_total_price(self, obj):
        """Calcule le total partiel (uniquement les produits du vendeur)"""
        user = self.context['request'].user
        if not hasattr(user, 'vendor'):
            return 0.0

        items = obj.items.filter(product__vendor=user.vendor)
        return sum(item.price * item.quantity for item in items)



class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

    def validate_status(self, value):
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError("Statut non valide.")
        return value

class ExportOrderPDFAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, customer=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Commande introuvable."}, status=404)

        pdf_buffer = generate_invoice(order)
        filename = f"commande_{order.order_number}.pdf"
        return FileResponse(pdf_buffer, as_attachment=True, filename=filename)