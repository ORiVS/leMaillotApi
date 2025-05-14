from datetime import timedelta
from email.message import EmailMessage

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.permissions import IsCustomer
from django.core.mail import EmailMessage
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from .permissions import IsVendor
from .serializers import RegisterUserSerializer, RegisterVendorSerializer, UserSerializer, UserProfileSerializer, \
    VerifyOTPSerializer

from vendor.models import Vendor
from accounts.models import User, UserProfile
from .tokens import account_activation_token
from .utils import send_verification_code_sms, send_verification_code_email


@swagger_auto_schema(
    method='post',
    request_body=RegisterUserSerializer,
    responses={201: 'Utilisateur créé', 400: 'Erreur de validation'}
)
@api_view(['POST'])
def registerUser(request):
    serializer = RegisterUserSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        print(serializer.errors)
        return Response({'message': 'Utilisateur créé avec succès'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=RegisterVendorSerializer,
    responses={201: 'Vendeur créé', 400: 'Erreur de validation'}
)
@api_view(['POST'])
def registerVendor(request):
    serializer = RegisterVendorSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Vendeur créé avec succès'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=RegisterVendorSerializer,
    responses={200: 'Vous êtes maintenant vendeur', 400: 'Erreur'}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registerVendor(request):
    user = request.user

    if user.role == 'VENDOR':
        return Response({'error': 'Vous êtes déjà vendeur.'}, status=400)

    serializer = RegisterVendorSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # Crée la boutique (Vendor)
        Vendor.objects.create(
            user=user,
            vendor_name=serializer.validated_data['vendor_name'],
            phone_number=serializer.validated_data['phone_number']
        )

        # Crée la boutique (Vendor)
        Vendor.objects.create(
            user=user,
            user_profile=user.userprofile,
            vendor_name=vendor_name,
            phone_number=phone_number
        )

        # Met à jour le rôle
        user.role = 'VENDOR'
        user.save()
        return Response({'message': 'Vous êtes maintenant vendeur.'}, status=200)
    return Response(serializer.errors, status=400)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh'],
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: 'Déconnexion réussie', 400: 'Erreur'}
)
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

User = get_user_model()

"""
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save()
            return HttpResponse("<h2>🎉 Compte activé avec succès !</h2>")
        else:
            return HttpResponse("<h2>✅ Ce compte est déjà activé.</h2>")
    else:
        return HttpResponse("<h2>⚠️ Lien invalide ou expiré.</h2>")

"""

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING, format='email')
        }
    ),
    responses={200: 'Email envoyé', 404: 'Utilisateur introuvable'}
)
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email requis.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        current_site = get_current_site(request)
        mail_subject = "Réinitialisez votre mot de passe"
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"http://{current_site.domain}/accounts/reset-password/{uid}/{token}/"
        message = render_to_string('accounts/emails/reset_password_email.html', {
            'user': user,
            'reset_url': reset_url,
        })
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.content_subtype = "html"
        email.send()
        return Response({'message': 'Un email de réinitialisation a été envoyé.'})
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['password'],
        properties={
            'password': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: 'Mot de passe réinitialisé', 400: 'Lien ou token invalide'}
)
@api_view(['POST'])
def reset_password(request, uidb64, token):
    password = request.data.get('password')
    if not password:
        return Response({'error': 'Nouveau mot de passe requis.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({'error': 'Lien invalide.'}, status=status.HTTP_400_BAD_REQUEST)

    if default_token_generator.check_token(user, token):
        user.set_password(password)
        user.save()
        return Response({'message': 'Mot de passe réinitialisé avec succès !'})
    else:
        return Response({'error': 'Token invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email', 'code'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'code': openapi.Schema(type=openapi.TYPE_STRING)
        }
    ),
    responses={200: 'Compte activé', 400: 'Code invalide'}
)
@api_view(['POST'])
def verify_code(request):
    email = request.data.get('email')
    code = request.data.get('code')

    try:
        user = User.objects.get(email=email, verification_code=code)

        if user.code_sent_at and timezone.now() - user.code_sent_at > timedelta(minutes=10):
            return Response({'error': 'Le code a expiré.'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = True
        user.is_verified = True
        user.verification_code = None
        user.save()
        return Response({'message': 'Compte activé avec succès.'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Code invalide ou utilisateur non trouvé.'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(type=openapi.TYPE_STRING),
            'method': openapi.Schema(type=openapi.TYPE_STRING, enum=['email', 'phone'])
        }
    ),
    responses={200: 'Code renvoyé', 404: 'Utilisateur introuvable'}
)
@api_view(['POST'])
def resend_code(request):
    email = request.data.get('email')
    method = request.data.get('method', 'email')  # 'email' ou 'phone'

    try:
        user = User.objects.get(email=email)
        user.generate_verification_code()

        if method == 'phone':
            send_verification_code_sms(user)
        else:
            send_verification_code_email(user)

        return Response({'message': 'Code renvoyé avec succès.'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

class VerifyOTPView(APIView):
    @swagger_auto_schema(
        request_body=VerifyOTPSerializer,
        responses={200: 'Compte vérifié', 400: 'Erreur de validation'}
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Compte vérifié avec succès ✅"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
