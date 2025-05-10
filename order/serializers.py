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


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    vendor_name = serializers.CharField(source='product.vendor.vendor_name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product', 'product_name', 'vendor_name', 'quantity', 'price']
        read_only_fields = ['price']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'total_price', 'created_at', 'items']
        read_only_fields = ['id', 'customer', 'status', 'total_price', 'created_at']

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("La commande doit contenir au moins un produit.")
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        customer = self.context['request'].user
        total_price = 0

        order = Order.objects.create(customer=customer, total_price=0)

        for item in items_data:
            product_id = item.get('product')
            quantity = item.get('quantity', 1)

            try:
                product = Product.objects.get(id=product_id, is_available=True)
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Produit invalide ou indisponible : ID {product_id}")

            # ✅ Vérifie le stock disponible
            if product.stock < quantity:
                raise serializers.ValidationError(
                    f"Stock insuffisant pour le produit '{product.product_name}' (stock actuel : {product.stock})"
                )

            price = product.price
            total_price += price * quantity

            # ✅ Création de l'item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            # ✅ Mise à jour du stock produit
            product.stock -= quantity
            product.save()

        order.total_price = total_price
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

    class Meta:
        model = Order
        fields = ['id', 'customer_email', 'total_price', 'status', 'created_at', 'items', 'status_history']

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
        elements.append(Paragraph(f"<b>Client :</b> {order.customer.get_full_name()} ({order.customer.email})", styles['Normal']))
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

        doc.build(elements)
        return response