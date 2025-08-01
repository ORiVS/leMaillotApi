from django.urls import path
from . import views
from .views import (
    PublicCategoryListAPIView, ProductListCreateAPIView, ProductRetrieveUpdateDestroyAPIView,
    PublicProductListAPIView, UploadProductImageAPIView, PublicProductDetailAPIView,
    DeleteProductImageAPIView, ProductImageListAPIView, PublicProductImageListAPIView,
    UploadMultipleProductImagesAPIView, ProductImageUpdateAPIView, DeleteProductImageAPIView,
    review_summary, ProductReviewViewSet
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'products/(?P<product_id>\d+)/reviews', ProductReviewViewSet, basename='product-reviews')

urlpatterns = [
    path('store/categories/', PublicCategoryListAPIView.as_view(), name='public-category-list'),
    path('products/', views.ProductListCreateAPIView.as_view(), name='api-product-list-create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroyAPIView.as_view(), name='api-product-detail'),
    path('store/products/', PublicProductListAPIView.as_view(), name='public-product-list'),
    path('products/<int:pk>/upload-image/', UploadProductImageAPIView.as_view(), name='upload-product-image'),
    path('products/images/<int:pk>/delete/', DeleteProductImageAPIView.as_view(), name='delete-product-image'),
    path('products/<int:pk>/images/', ProductImageListAPIView.as_view(), name='product-image-list'),
    path('store/products/<int:pk>/images/', PublicProductImageListAPIView.as_view(), name='public-product-image-list'),
    path('products/<int:pk>/upload-images/', UploadMultipleProductImagesAPIView.as_view(), name='upload-multiple-images'),
    path('products/images/<int:pk>/update/', ProductImageUpdateAPIView.as_view(), name='update-product-image'),
    path('store/products/<int:pk>/', PublicProductDetailAPIView.as_view(), name='public-product-detail'),
    path('products/<int:product_id>/reviews/summary/', review_summary),
]

urlpatterns += router.urls
