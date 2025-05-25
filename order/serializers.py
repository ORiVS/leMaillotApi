from django.http import HttpResponse
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



class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    vendor_name = serializers.CharField(source='product.vendor.vendor_name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'vendor_name', 'quantity', 'price']
        read_only_fields = ['price']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    delivery_latitude = serializers.FloatField(required=False)
    delivery_longitude = serializers.FloatField(required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'status', 'delivery_method',
             'delivery_latitude', 'delivery_longitude',
            'delivery_cost', 'total_price', 'created_at', 'items'
        ]
        read_only_fields = ['customer', 'status', 'delivery_cost', 'total_price', 'created_at']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("La commande doit contenir au moins un produit.")
        return items

    def validate(self, data):
        if data.get("delivery_method") == "delivery":
            if not data.get("delivery_latitude") or not data.get("delivery_longitude"):
                raise serializers.ValidationError("Coordonnées GPS requises pour la livraison.")
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = self.context['request'].user
        request = self.context.get('request')

        delivery_method = request.data.get('delivery_method', 'pickup')
        delivery_latitude = request.data.get('delivery_latitude')
        delivery_longitude = request.data.get('delivery_longitude')

        delivery_cost = 0.0
        total_price = 0

        # ➕ Crée la commande vide, à compléter ensuite
        order = Order.objects.create(
            customer=customer,
            delivery_method=delivery_method,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            delivery_cost=0.0,
            total_price=0
        )

        vendor_ids = set()

        for item in items_data:
            product_id = item.get('product')
            quantity = item.get('quantity', 1)

            try:
                product = Product.objects.get(id=product_id, is_available=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Produit invalide ou indisponible : ID {product_id}")

            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour le produit '{product.product_name}' (stock actuel : {product.stock})"
                )

            price = product.price
            total_price += price * quantity

            # ➕ Ajout de l'article
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            # ➖ Mise à jour du stock
            product.stock -= quantity
            product.save()

            vendor_ids.add(product.vendor.id)

        # 🛵 Frais de livraison si mode "delivery"
        if delivery_method == 'delivery':
            from vendor.models import Vendor
            for vid in vendor_ids:
                vendor = Vendor.objects.get(id=vid)
                delivery_cost += float(vendor.delivery_fee)

        order.delivery_cost = delivery_cost
        order.total_price = Decimal(total_price) + Decimal(delivery_cost)
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

    class Meta:
        model = Order
        fields = [
            'id', 'customer_email', 'total_price', 'delivery_cost', 'delivery_method',
            'status', 'created_at', 'items', 'status_history', 'order_number'
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
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")

        if order.customer != request.user and not request.user.is_staff:
            return HttpResponse("Non autorisé", status=403)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="facture_commande_{order.id}.pdf"'

        buffer = []
        doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

        styles = getSampleStyleSheet()
        elements = []

        # ✅ Titre
        elements.append(Paragraph(f"<b>FACTURE</b> – Commande #{order.id}", styles['Title']))
        elements.append(Spacer(1, 12))

        # ✅ Infos client
        elements.append(Paragraph(f"<b>Client :</b> {order.customer.first_name} {order.customer.last_name} ({order.customer.email})", styles['Normal']))
        elements.append(Paragraph(f"<b>Date :</b> {order.created_at.strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # ✅ Tableau des produits
        data = [["Produit", "Vendeur", "Quantité", "Prix unitaire (€)", "Total (€)"]]
        for item in order.items.all():
            row = [
                item.product.product_name,
                item.product.vendor.vendor_name,
                item.quantity,
                f"{item.price:.2f}",
                f"{item.quantity * item.price:.2f}"
            ]
            data.append(row)

        table = Table(data, colWidths=[100, 80, 50, 80, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))

        # ✅ Total
        elements.append(Paragraph(f"<b>Total à payer :</b> {order.total_price:.2f} €", styles['Heading2']))
        # 🛵 Méthode de livraison
        elements.append(Paragraph(
            f"<b>Mode de livraison :</b> {'Livraison à domicile' if order.delivery_method == 'delivery' else 'Retrait en boutique'}",
            styles['Normal']))
        elements.append(Paragraph(f"<b>Frais de livraison :</b> {order.delivery_cost:.2f} €", styles['Normal']))
        elements.append(Spacer(1, 12))

        doc.build(elements)
        return response