from django.urls import path
from . import views
from .views import PublicCategoryListAPIView, ProductListCreateAPIView, ProductRetrieveUpdateDestroyAPIView, PublicProductListAPIView

urlpatterns = [
    path('store/categories/', PublicCategoryListAPIView.as_view(), name='public-category-list'),
    path('products/', views.ProductListCreateAPIView.as_view(), name='api-product-list-create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroyAPIView.as_view(), name='api-product-detail'),
    path('store/products/', PublicProductListAPIView.as_view(), name='public-product-list'),

]
