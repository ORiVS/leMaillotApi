from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import WishlistItem
from .serializers import WishlistItemSerializer
from category.models import Product

class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        items = WishlistItem.objects.filter(user=request.user)
        serializer = WishlistItemSerializer(items, many=True)
        return Response(serializer.data)

    def create(self, request):
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({'error': 'product_id is required'}, status=400)
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({'error': 'Product not found'}, status=404)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            return Response({'message': 'Already in wishlist'}, status=200)
        return Response(WishlistItemSerializer(item).data, status=201)

    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        item = WishlistItem.objects.filter(id=pk, user=request.user).first()
        if not item:
            return Response({'error': 'Item not found'}, status=404)
        item.delete()
        return Response({'message': 'Removed from wishlist'})
