import google
from django.contrib.auth import authenticate
from django.test import TestCase
from django.urls import reverse
from google.auth import credentials

# from phone_verify.models import SMSVerification
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase, APIClient

from profiles.models import UserProfile
from servicies.choices import LoginChoices
from users.models import User, TokenCode
from users.serializers import (
    RegistrationSerializer,
    AuthenticationSerializer,
    LoginSerializer,
)

USER = {
    "username": "marlon.brando",
    "phone": "+393347676270",
    "email": "brando@email.com",
    "password": "123",
}

USER_NAME = "Marlon Brando"
USER_PASSWORD = USER["password"]

LOGIN_USER = {"username": USER["username"], "password": USER["password"]}

GUEST_USER = {
    "username": "Caravaggio",
    "email": "caravaggio@email.com",
    "password": "123car",
}

REGISTER_USER = {
    "username": "charlotte",
    "password": "12345678",
    "name": "Charlotte V.",
}

REGISTER_GUEST_USER = {
    "username": "Charles",
    "password": "12345678",
    "name": "Charles de Gaulle",
}


class UserTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(**USER)
        self.guest_user = User.objects.create_user(**GUEST_USER)
        self.token_code = TokenCode.objects.create(username=self.user.username)

    def login(self, username):
        return self.client.login(username=username, password=USER_PASSWORD)

    def test_password(self):
        is_valid = self.user.check_password(USER_PASSWORD)
        self.assertTrue(is_valid)

    def test_authenticate(self):
        user = authenticate(username=self.user.username, password=USER_PASSWORD)
        self.assertTrue(user is not None)

        user = authenticate(username=self.user.username, password="")
        self.assertIsNone(user)

        user = authenticate(username="", password="")
        self.assertIsNone(user)

    def test_login_using_username(self):
        logged = self.login(username=self.user.username)
        self.assertTrue(logged)

    def test_login_using_email(self):
        logged = self.login(username=self.user.email)
        self.assertTrue(logged)

    def test_login_using_phone(self):
        logged = self.login(username=self.user.phone)
        self.assertTrue(logged)

    def test_user_string_representation(self):
        user = self.user
        self.assertEqual(str(user), f"{user.id} • {user.username}")

    # TokenCode - Phone OTP
    def test_create_token_code(self):
        token = TokenCode.objects.update_or_create(username=self.user.username)
        self.assertEqual(token.username, self.user.username)

        token = TokenCode.objects.update_or_create(username=self.guest_user.username)
        self.assertEqual(token.username, self.guest_user.username)

    ##### Why test works only when the function is invoked?
    def test_delete_token_code(self):
        TokenCode.objects.delete_for(self.user)


class SerializerTestCase(APITestCase):
    def test_registration(self):
        serializer = RegistrationSerializer(data=USER)

        self.assertTrue(serializer.is_valid())
        self.user = serializer.save(name=USER_NAME)

        serializer = RegistrationSerializer(data=USER)
        self.assertFalse(serializer.is_valid())

    def test_auth(self):
        User.objects.create_user(**USER)

        serializer = AuthenticationSerializer(data=LOGIN_USER)

        self.assertTrue(serializer.is_valid())

        serializer = AuthenticationSerializer(data=GUEST_USER)
        self.assertFalse(serializer.is_valid())

    def test_login(self):
        user = User.objects.create_user(**USER)
        profile = UserProfile.objects.create(user=user, name=USER_NAME)

        serializer = LoginSerializer(profile)
        data = serializer.data

        user_id = data.get("id")
        self.assertEqual(user.id, user_id)


class ViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        self.client = APIClient()

    def get_user(self):
        return User.objects.create_user(**USER)

    def get_token_code(self, username):
        return TokenCode.objects.update_or_create(username=username)

    def get_user_profile(self, user):
        return UserProfile.objects.create(user=user, name=USER_NAME)

    def test_register(self):
        url = reverse("register")

        # Test successful registration

        # Request OTP token to verify phone or email
        token = self.get_token_code(REGISTER_USER["username"])

        post_data = {**REGISTER_USER, "token_value": token.value, "code": token.code}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # RegistrationSerializer failed because username already exists

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        # RegistrationSerializer succeed, TokenCode does not exists

        post_data = {
            **REGISTER_GUEST_USER,
            "token_value": "this_is_a_token",
            "code": "55555",
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_login(self):
        url = reverse("login")

        user = self.get_user()
        self.get_user_profile(user)

        response = self.client.post(url, LOGIN_USER)
        self.assertTrue(response.status_code, HTTP_200_OK)

        response = self.client.post(url, {})
        self.assertTrue(response.status_code, HTTP_400_BAD_REQUEST)

    def test_check_user_existence(self):
        url = reverse("check_user_existence")

        user = self.get_user()

        # Test using username

        post_data = {"username": user.username}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Test using email

        post_data = {"email": USER["email"]}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Test using phone

        post_data = {"phone": USER["phone"]}

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Test using empty data -> fail

        response = self.client.post(url, {})
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_request_otp(self):
        user = self.get_user()

        url = reverse("request_otp")

        # Test email or phone

        params = {"username": user.email}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_200_OK)

        # Test fail to found TokenCode

        params = {"username": "this_username_does_not_exist"}
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_resend_otp(self):
        url = reverse("resend_otp")
        user = self.get_user()

        token_code = self.get_token_code(user.email)

        data = {"token_value": token_code.value}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"token_value": "this_token_does_not_exist"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_verify_otp(self):
        url = reverse("verify_otp")
        user = self.get_user()

        token_code = self.get_token_code(user.email)

        data = {
            "username": user.email,
            "token_value": token_code.value,
            "code": token_code.code,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"username": "this_username_does_not_exist"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_reset_password(self):
        url = reverse("reset_password")
        user = self.get_user()
        token_code = self.get_token_code(user.email)

        data = {
            "token_value": token_code.value,
            "new_password": "this_is_my_new_password",
        }
        response = self.client.post(url, data)
        self.assertTrue(response.status_code, HTTP_200_OK)

        data = {"token_value": "this_token_value_does_not_exist"}
        response = self.client.post(url, data)
        self.assertTrue(response.status_code, HTTP_404_NOT_FOUND)

    def test_get_recent_users(self):
        url = reverse("get_recent_users")

        user = self.get_user()
        self.get_user_profile(user)
        self.client.force_authenticate(user)

        params = {"value": "type_username_here"}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_200_OK)

        params = {"value": ""}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_search_users(self):
        url = reverse("search_users")

        user = self.get_user()
        self.get_user_profile(user)
        self.client.force_authenticate(user)

        params = {"value": "search_username", "offset": 0}

        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_phone_verification_register(self):
        register_url = reverse("phone_verification_register")

        phone_number = USER["phone"]
        data = {"phone_number": phone_number}
        response = self.client.post(register_url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        verify_url = reverse("phone_verification_verify")

        session_token = response.data.get("session_token")
        sms_verification = (
            None  # SMSVerification.objects.filter(phone_number=phone_number).first()
        )
        security_code = sms_verification.security_code

        data = {
            "phone_number": USER["phone"],
            "session_token": session_token,
            "security_code": security_code,
        }

        response = self.client.post(verify_url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"phone_number": "invalid_phone_number"}
        response = self.client.post(register_url, data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_social_login(self):
        url = reverse("social_login")

        data = {"username": USER["email"], "login_method": LoginChoices.FACEBOOK}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        data = {"username": USER["email"], "login_method": LoginChoices.GOOGLE}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_social_profile_existence(self):
        url = reverse("check_profile_existence")

        data = {"login_method": LoginChoices.FACEBOOK}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        data = {"login_method": LoginChoices.GOOGLE}
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
