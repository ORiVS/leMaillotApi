from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User  # <- personnalisé



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
    return Response({'message': 'Vendeur créé avec succès'}, status=status.HTTP_201_CREATED)

# Connexion avec retour des tokens JWT
@api_view(['POST'])
def loginUser(request):
    email = request.data.get('email')
    password = request.data.get('password')

    try:
        user = User.objects.get(email=email)
        if user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'role': user.get_role_display(),
                'email': user.email,
                'username': user.username,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

# Déconnexion = Blacklist du refresh token
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logoutUser(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({'error': 'Token invalide ou déjà blacklisted'}, status=status.HTTP_400_BAD_REQUEST)

