from django.urls import path
from . import views
from .views import get_me, activate_account

urlpatterns = [
    path('registerUser/', views.registerUser, name='registerUser'),
    path('registerVendor/', views.registerVendor, name='registerVendor'),

    path('login/', views.login, name='login'),

    path('logout/', views.logout, name='logout'),

    path('me/', get_me, name='get_me'),

    path('activate/<uidb64>/<token>/', activate_account, name='activate'),

]