from datetime import timezone, timedelta

from rest_framework import serializers, request
from accounts.models import User, UserProfile
from accounts.utils import send_verification_code_email, send_verification_code_sms
from vendor.models import Vendor

class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'username', 'email', 'password']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d’utilisateur existe déjà")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.role = User.CUSTOMER
        user.is_active = False
        user.generate_verification_code()

        request = self.context.get('request')
        method = request.data.get('verification_method', 'email') if request else 'email'

        if method == 'phone':
            send_verification_code_sms(user)
        else:
            send_verification_code_email(user)

        user.save()

        return user

class RegisterVendorSerializer(RegisterUserSerializer):
    vendor_license = serializers.FileField(write_only=True)

    class Meta(RegisterUserSerializer.Meta):
        fields = RegisterUserSerializer.Meta.fields + ['vendor_license']

    def create(self, validated_data):
        # ⚠️ Retirer vendor_license du dict pour éviter l'erreur
        request = self.context.get('request')
        vendor_license = request.FILES.get('vendor_license') if request else None

        # Supprimer le champ du validated_data pour éviter l'erreur
        if 'vendor_license' in validated_data:
            validated_data.pop('vendor_license')

        # Création de l'utilisateur (sans vendor_license)
        user = super(RegisterVendorSerializer, self).create(validated_data)
        user.role = User.VENDOR
        user.is_staff = True
        user.save()

        # Création du vendeur avec la licence
        Vendor.objects.create(
            user=user,
            user_profile=user.userprofile,
            vendor_name=f"{user.first_name} {user.last_name}",
            vendor_license=vendor_license
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone_number', 'role', 'role_display']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = ['user']


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField()

    def validate(self, data):
        phone = data['phone_number']
        code = data['code']
        try:
            user = User.objects.get(phone_number=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur non trouvé.")

        if user.verification_code != code:
            raise serializers.ValidationError("Code incorrect.")

        if user.code_sent_at and timezone.now() > user.code_sent_at + timedelta(minutes=10):
            raise serializers.ValidationError("Code expiré.")

        data['user'] = user
        return data

    def save(self, **kwargs):
        user = self.validated_data['user']
        user.is_verified = True
        user.verification_code = None
        user.code_sent_at = None
        user.save()
        return user