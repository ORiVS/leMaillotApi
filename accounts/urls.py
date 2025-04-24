from django.urls import path
from . import views
from .views import get_me, activate_account, reset_password, forgot_password

urlpatterns = [
    path('registerUser/', views.registerUser, name='registerUser'),
    path('registerVendor/', views.registerVendor, name='registerVendor'),

    path('login/', views.login, name='login'),

    path('logout/', views.logout, name='logout'),

    path('me/', get_me, name='get_me'),

    path('activate/<uidb64>/<token>/', activate_account, name='activate'),

    path('forgot-password/', forgot_password, name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset-password'),
]