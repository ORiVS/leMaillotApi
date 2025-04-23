from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterUserSerializer, RegisterVendorSerializer

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

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Connexion réussie'
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Mot de passe incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=status.HTTP_404_NOT_FOUND)

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
