from django.urls import path
from . import views
from .views import get_me

urlpatterns = [
    path('registerUser/', views.registerUser, name='registerUser'),
    path('registerVendor/', views.registerVendor, name='registerVendor'),

    path('login/', views.login, name='login'),

    path('logout/', views.logout, name='logout'),

    path('me/', get_me, name='get_me'),
]