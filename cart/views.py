from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Cart, CartItem
from category.models import Product
from .serializers import CartSerializer, CartItemSerializer

class CartDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

class AddToCartAPIView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return Response({'error': 'Produit introuvable ou indisponible'}, status=404)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartItemSerializer(cart_item).data, status=201)

class RemoveFromCartAPIView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=request.user).first()
        product_id = request.data.get('product')

        if not cart:
            return Response({'error': 'Aucun panier trouvé'}, status=404)

        item = cart.items.filter(product_id=product_id).first()
        if not item:
            return Response({'error': 'Produit non présent dans le panier'}, status=404)

        item.delete()
        return Response({'message': 'Produit retiré du panier'}, status=200)

class UpdateCartItemQuantityAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        product_id = request.data.get('product')
        quantity = request.data.get('quantity')

        if not product_id or quantity is None:
            return Response({"error": "Product ID et quantity sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Produit introuvable."}, status=status.HTTP_404_NOT_FOUND)

        try:
            cart_item = CartItem.objects.get(user=user, product=product)
        except CartItem.DoesNotExist:
            return Response({"error": "Ce produit n’est pas dans votre panier."}, status=status.HTTP_404_NOT_FOUND)

        if quantity < 1:
            cart_item.delete()
            return Response({"message": "Produit supprimé du panier car la quantité est inférieure à 1."}, status=status.HTTP_200_OK)

        cart_item.quantity = quantity
        cart_item.save()
        return Response({"message": "Quantité mise à jour avec succès."}, status=status.HTTP_200_OK)

class CartTotalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"total": 0.0}, status=status.HTTP_200_OK)

        total = sum(item.product.price * item.quantity for item in cart_items)

        return Response({"total": float(total)}, status=status.HTTP_200_OK)

class ClearCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        CartItem.objects.filter(user=user).delete()
        return Response({"message": "Panier vidé avec succès."}, status=status.HTTP_200_OK)