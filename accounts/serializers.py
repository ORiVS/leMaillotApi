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

class RegisterVendorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Vendor
        fields = ['vendor_name', 'description', 'address', 'city', 'latitude', 'longitude']

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