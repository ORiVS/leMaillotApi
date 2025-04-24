from rest_framework import serializers, request
from accounts.models import User, UserProfile
from accounts.utils import send_verification_email
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
        user.save()

        #send email verification
        request = self.context.get('request')
        send_verification_email(request, user)

        return user

class RegisterVendorSerializer(RegisterUserSerializer):
    vendor_license = serializers.FileField(write_only=True)

    class Meta(RegisterUserSerializer.Meta):
        fields = RegisterUserSerializer.Meta.fields + ['vendor_license']

    def create(self, validated_data):
        vendor_license = validated_data.pop('vendor_license')
        user = super(RegisterVendorSerializer, self).create(validated_data)

        user.role = User.VENDOR
        user.is_staff = True
        user.save()

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