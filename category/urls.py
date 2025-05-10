from django.urls import path
from . import views
from .views import PublicProductListAPIView

urlpatterns = [
    path('categories/', views.CategoryListCreateAPIView.as_view(), name='api-category-list-create'),
    path('products/', views.ProductListCreateAPIView.as_view(), name='api-product-list-create'),
    path('categories/<int:pk>/', views.CategoryRetrieveUpdateDestroyAPIView.as_view(), name='api-category-detail'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroyAPIView.as_view(), name='api-product-detail'),
    path('store/products/', PublicProductListAPIView.as_view(), name='public-product-list'),

]
