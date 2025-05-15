from django.utils.dateparse import parse_date
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, NotFound

from .models import Order, OrderStatusHistory
from .serializers import OrderCreateSerializer, OrderDetailSerializer, OrderStatusUpdateSerializer, ExportOrderPDFAPIView
from cart.models import CartItem

class OrderCreateAPIView(generics.CreateAPIView):
    serializer_class = OrderCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        delivery_method = self.request.data.get('delivery_method', 'pickup')
        delivery_cost = 0.0

        if delivery_method == 'delivery':
            # Récupérer les produits du panier de l'utilisateur
            cart_items = CartItem.objects.filter(cart__user=user)

            # Calculer les frais par vendeur unique
            vendor_ids = set()
            for item in cart_items:
                vendor_ids.add(item.product.vendor.id)

            for vid in vendor_ids:
                vendor = Vendor.objects.get(id=vid)
                delivery_cost += float(vendor.delivery_fee)

        # Sauvegarder la commande avec les données de livraison
        serializer.save(
            customer=user,
            delivery_method=delivery_method,
            delivery_cost=delivery_cost,
        )

class OrderListAPIView(generics.ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')

class OrderStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        order = super().get_object()
        user = self.request.user

        if user.is_staff:
            return order

        if user.role == "VENDOR":
            if order.items.filter(product__vendor=user.vendor).exists():
                return order
            raise PermissionDenied("Vous n'avez pas le droit de modifier cette commande.")

        raise PermissionDenied("Accès réservé aux vendeurs ou administrateurs.")

    def perform_update(self, serializer):
        order = self.get_object()
        old_status = order.status
        new_status = serializer.validated_data['status']

        # Sauvegarde de l'historique
        OrderStatusHistory.objects.create(
            order=order,
            previous_status=old_status,
            new_status=new_status,
            changed_by=self.request.user
        )

        serializer.save()  # met à jour le statut

class VendorOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'vendor'):
            raise PermissionDenied("Accès réservé aux vendeurs.")

        queryset = Order.objects.filter(items__product__vendor=user.vendor).distinct()

        # 🔍 Filtres GET
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        created_after = self.request.query_params.get('created_after')
        if created_after:
            try:
                date = parse_date(created_after)
                queryset = queryset.filter(created_at__gte=date)
            except:
                pass

        created_before = self.request.query_params.get('created_before')
        if created_before:
            try:
                date = parse_date(created_before)
                queryset = queryset.filter(created_at__lte=date)
            except:
                pass

        return queryset.order_by('-created_at')

class VendorOrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'vendor'):
            raise PermissionDenied("Accès réservé aux vendeurs.")
        return Order.objects.filter(items__product__vendor=user.vendor).distinct()

    def get_object(self):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=self.kwargs['pk'])
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable ou non accessible.")

class AdminOrderListAPIView(generics.ListAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_staff:
            raise PermissionDenied("Accès réservé aux administrateurs.")

        queryset = Order.objects.all()

        # Filtres GET
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        created_after = self.request.query_params.get('created_after')
        if created_after:
            try:
                date = parse_date(created_after)
                queryset = queryset.filter(created_at__gte=date)
            except:
                pass

        created_before = self.request.query_params.get('created_before')
        if created_before:
            try:
                date = parse_date(created_before)
                queryset = queryset.filter(created_at__lte=date)
            except:
                pass

        return queryset.order_by('-created_at')


class CustomerOrderDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=self.kwargs['pk'])
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable ou non autorisée.")