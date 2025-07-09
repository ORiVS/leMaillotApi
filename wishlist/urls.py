from django.urls import path
from .views import WishlistViewSet

wishlist_list = WishlistViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

wishlist_remove = WishlistViewSet.as_view({
    'delete': 'remove'
})

urlpatterns = [
    path('wishlist/', wishlist_list, name='wishlist-list'),
    path('wishlist/<int:pk>/remove/', wishlist_remove, name='wishlist-remove'),
]
