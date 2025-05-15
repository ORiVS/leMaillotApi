from django.urls import path
from .views import CartDetailAPIView, AddToCartAPIView, RemoveFromCartAPIView

urlpatterns = [
    path('', CartDetailAPIView.as_view(), name='cart-detail'),
    path('add/', AddToCartAPIView.as_view(), name='cart-add'),
    path('remove/', RemoveFromCartAPIView.as_view(), name='cart-remove'),
    path('update/', UpdateCartItemQuantityAPIView.as_view(), name='cart-update-item'),
    path('total/', CartTotalAPIView.as_view(), name='cart-total'),
    path('clear/', ClearCartAPIView.as_view(), name='cart-clear'),

]
