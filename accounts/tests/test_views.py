from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile

class AuthViewTests(APITestCase):

    def setUp(self):
        self.register_user_url = reverse('registerUser')
        self.register_vendor_url = reverse('registerVendor')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')

    def test_register_user_success(self):
        data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "username": "testuser",
            "phone_number": "22990000000",
            "password": "securepass123"
        }
        response = self.client.post(self.register_user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_user_duplicate_email(self):
        User.objects.create_user(email="duplicate@example.com", username="dupuser", password="pass")
        data = {
            "first_name": "Dup",
            "last_name": "User",
            "email": "duplicate@example.com",
            "username": "newuser",
            "phone_number": "22991111111",
            "password": "newpass"
        }
        response = self.client.post(self.register_user_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_vendor_success(self):
        file = SimpleUploadedFile("license.pdf", b"file_content", content_type="application/pdf")
        data = {
            "first_name": "Vendor",
            "last_name": "Test",
            "email": "vendor@example.com",
            "username": "vendortest",
            "phone_number": "22992222222",
            "password": "vendorpass123",
            "vendor_license": file
        }
        response = self.client.post(self.register_vendor_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(role=User.VENDOR).count(), 1)

    def test_login_success(self):
        user = User.objects.create_user(email="login@example.com", username="loginuser", password="loginpass")
        data = {"email": "login@example.com", "password": "loginpass"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_failure_wrong_password(self):
        User.objects.create_user(email="fail@example.com", username="failuser", password="rightpass")
        data = {"email": "fail@example.com", "password": "wrongpass"}
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        user = User.objects.create_user(email="logout@example.com", username="logoutuser", password="logoutpass")
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_token(self):
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class MeViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="me@example.com",
            username="meuser",
            first_name="Me",
            last_name="User",
            phone_number="22991111111",
            password="securepass"
        )
        self.url = reverse('get_me')
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_me_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.user.email)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertIn('profile', response.data)

    def test_get_me_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)