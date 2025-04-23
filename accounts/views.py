from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .permissions import IsVendor
from .serializers import RegisterUserSerializer, RegisterVendorSerializer, UserSerializer, UserProfileSerializer

from vendor.models import Vendor
from accounts.models import User, UserProfile

@api_view(['POST'])
def registerUser(request):
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def registerVendor(request):
    serializer = RegisterVendorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Vendeur créé avec succès'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    user = authenticate(request, email=email, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Connexion réussie'
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Email ou mot de passe invalide'}, status=status.HTTP_401_UNAUTHORIZED)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Une erreur s\'est produite'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsVendor])
def vendor_dashboard(request):
    return Response({'message': 'Bienvenue sur le dashboard vendeur'})

from accounts.permissions import IsCustomer

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomer])
def customer_dashboard(request):
    return Response({'message': 'Bienvenue sur le dashboard client'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_me(request):
    user = request.user
    user_profile = user.userprofile

    user_data = UserSerializer(user).data
    profile_data = UserProfileSerializer(user_profile).data

    return Response({
        'user': user_data,
        'profile': profile_data
    })