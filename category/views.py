from django.db.models import Q
from rest_framework import generics, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from accounts.permissions import IsVendor
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Category, Product, ProductImage, ProductReview
from .serializers import CategorySerializer, ProductSerializer, ProductImageSerializer, ProductReviewSerializer
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.generics import DestroyAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view

# 🔓 Vue publique pour afficher toutes les catégories
class PublicCategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all().order_by('category_name')
    serializer_class = CategorySerializer
    permission_classes = []

class BaseVendorProtectedView:
    def get_vendor_or_403(self):
        try:
            return self.request.user.vendor
        except Exception:
            raise PermissionDenied("Aucun profil vendeur associé à ce compte.")


class ProductListCreateAPIView(BaseVendorProtectedView, generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.get_vendor_or_403())

    def perform_create(self, serializer):
        vendor = self.get_vendor_or_403()
        serializer.save(vendor=vendor)


class ProductRetrieveUpdateDestroyAPIView(BaseVendorProtectedView, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]

    def get_queryset(self):
        return Product.objects.filter(vendor=self.get_vendor_or_403())

class PublicProductListAPIView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = []
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)

        # 🔍 Filtres GET
        category_slugs = self.request.query_params.get('category')
        if category_slugs:
            slugs = category_slugs.split(',')
            queryset = queryset.filter(categories__slug__in=slugs).distinct()

        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        featured = self.request.query_params.get('featured')
        if featured == "true":
            queryset = queryset.filter(is_featured=True)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__category_name__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_serializer_context(self):
        return {'request': self.request}

class UploadProductImageAPIView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk, vendor=request.user.vendor)
        except Product.DoesNotExist:
            return Response({"error": "Produit introuvable ou non autorisé"}, status=403)

        image = request.FILES.get('image')
        alt_text = request.data.get('alt_text', '')

        if not image:
            return Response({"error": "Image manquante"}, status=400)

        ProductImage.objects.create(product=product, image=image, alt_text=alt_text)
        return Response({"message": "Image ajoutée avec succès"}, status=201)

class DeleteProductImageAPIView(DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def get_object(self):
        image_id = self.kwargs['pk']
        try:
            image = ProductImage.objects.select_related('product__vendor').get(pk=image_id)
        except ProductImage.DoesNotExist:
            raise NotFound("Image non trouvée")

        if image.product.vendor.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez supprimer que vos propres images")

        return image

    def destroy(self, request, *args, **kwargs):
        image = self.get_object()
        image.image.delete(save=False)  # supprime le fichier physique
        image.delete()
        return Response({"message": "Image supprimée avec succès"}, status=204)


class ProductImageListAPIView(generics.ListAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        product_id = self.kwargs['pk']

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise NotFound("Produit introuvable")

        # 🛡️ Si accès réservé aux vendeurs uniquement :
        if product.vendor.user != self.request.user:
            raise PermissionDenied("Accès interdit à ce produit")

        return ProductImage.objects.filter(product=product)

class PublicProductImageListAPIView(generics.ListAPIView):
    serializer_class = ProductImageSerializer
    permission_classes = []

    def get_queryset(self):
        product_id = self.kwargs['pk']
        return ProductImage.objects.filter(product_id=product_id, product__is_available=True)

class UploadMultipleProductImagesAPIView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # 🔐 Vérification du produit et de la propriété
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"error": "Produit introuvable"}, status=404)

        if product.vendor.user != request.user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres produits")

        # 📥 Récupération des fichiers
        files = request.FILES.getlist('images')  # clé 'images' dans FormData
        if not files:
            return Response({"error": "Aucune image reçue"}, status=400)

        created = 0
        for image_file in files:
            ProductImage.objects.create(product=product, image=image_file)
            created += 1

        return Response({"message": f"{created} image(s) ajoutée(s) avec succès"}, status=201)


class ProductImageUpdateAPIView(UpdateAPIView):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        image = super().get_object()
        if image.product.vendor.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres images")
        return image

class PublicProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_serializer_context(self):
        return {'request': self.request}


class ProductReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ProductReviewSerializer

    def get_permissions(self):
        if self.request.method in ['GET']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return ProductReview.objects.filter(product_id=self.kwargs['product_id'])

    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        if ProductReview.objects.filter(user=self.request.user, product_id=product_id).exists():
            raise ValidationError("Vous avez déjà laissé un avis pour ce produit.")
        serializer.save(product_id=product_id)

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("Vous ne pouvez pas supprimer cet avis.")
        instance.delete()

    def get_object(self):
        obj = super().get_object()
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj.user != self.request.user:
                raise PermissionDenied("Vous ne pouvez modifier que vos propres avis.")
        return obj


@api_view(['GET'])

def review_summary(request, product_id):
    reviews = ProductReview.objects.filter(product_id=product_id)
    average = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    total = reviews.count()
    distribution = reviews.values('rating').annotate(count=Count('id')).order_by('-rating')
    return Response({
        "average_rating": round(average, 2),
        "total_reviews": total,
        "distribution": {item['rating']: item['count'] for item in distribution}
    })