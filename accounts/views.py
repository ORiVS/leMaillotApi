from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib import messages
from rest_framework_simplejwt.tokens import RefreshToken

from vendor.models import Vendor
from accounts.models import User, UserProfile



#Enregistrement d'un utilisateur
@api_view(['POST'])
def registerUser(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_number = request.data.get('phone_number')
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({'error': 'Email et password requis'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Cet email est déjà utilisé'}, status=status.HTTP_409_CONFLICT)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Ce nom d’utilisateur existe déjà'}, status=status.HTTP_409_CONFLICT)

    user = User.objects.create_user(first_name=first_name, last_name=last_name, phone_number=phone_number, username=username, email=email, password=password)
    user.role = User.CUSTOMER
    user.save()
    messages.success(request, 'Votre compte a été créé avec succes')
    return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)

#Enregistrement d'un utilisateur
@api_view(['POST'])
def registerVendor(request):
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    phone_number = request.data.get('phone_number')
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    vendor_license = request.FILES.get('vendor_license')

    if not email or not password:
        return Response({'error': 'Email et password requis'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Cet email est déjà utilisé'}, status=status.HTTP_409_CONFLICT)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Ce nom d’utilisateur existe déjà'}, status=status.HTTP_409_CONFLICT)

    user = User.objects.create_user(first_name=first_name, last_name=last_name, phone_number=phone_number, username=username, email=email, password=password)
    user.role = User.VENDOR
    user.is_staff = True
    user.save()

    user_profile = user.userprofile
    vendor_name = f"{first_name} {last_name}"

    Vendor.objects.create(user=user, user_profile=user_profile, vendor_name=vendor_name, vendor_license=vendor_license)

    return Response({'message': 'Vendeur créé avec succès'}, status=status.HTTP_201_CREATED)
    print("📥 DATA =", request.data)
    print("📎 FILES =", request.FILES)
    print("📛 vendor_name =", vendor_name)

