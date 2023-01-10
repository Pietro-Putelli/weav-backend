from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.test import APITestCase, APIClient

from core.test_utilis import get_mocked_file
from profiles.models import UserProfile
from profiles.serializers import ShortUserProfileSerializer, ShortProfileSerializer
from users.models import User

USER = {
    "username": "andy.warhol",
    "phone": "+393347676270",
    "email": "andy@email.com",
    "password": "123"
}

USER_NAME = "Andy Warhol"

USER_PROFILE = {
    "name": USER_NAME,
    "bio": "Be wiser than other, if you can, but don't tell them so",
    "link": "https://www.sticazzi.com",
    "phone": USER["phone"],
    "email": USER["email"]
}


class ViewAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(**USER)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_user_profile(self):
        url = reverse("user_profile")

        UserProfile.objects.create(user=self.user, name=USER_NAME)

        params = {"user_id": self.user.id}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_200_OK)

        params = {"user_id": 100}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        data = {"name": "NEW NAME"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"username": "new_username"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_update_user_password(self):
        url = reverse("update_user_password")

        data = {"old_password": USER["password"], "new_password": "123456788"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"old_password": "wrong_old_password", "new_password": "12345"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_change_profile_picture(self):
        url = reverse("change_profile_picture")

        UserProfile.objects.create(user=self.user, name=USER_NAME)

        picture = get_mocked_file("profile.picture.png")
        data = {"picture": picture}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_block_user(self):
        url = reverse("block_user")
        UserProfile.objects.create(user=self.user, name=USER_NAME)

        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"user_id": self.user.id, "mode": "block"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = {"user_id": self.user.id, "mode": "unblock"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)


class ManagerAPITestCase(APITestCase):
    def test_profile_manager(self):
        user = User.objects.create_user(**USER)
        UserProfile.objects.create(user=user, name=USER_NAME)

        first_profile = UserProfile.objects.get(user=user)
        second_profile = UserProfile.objects.get_by(user)
        self.assertEqual(first_profile.id, second_profile.id)


class SerializerAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(**USER)

        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_short_profile(self):
        picture = get_mocked_file("profile.picture.png")
        profile = UserProfile.objects.create(user=self.user, name=USER_NAME, picture=picture)

        serializer = ShortUserProfileSerializer(self.user)
        data = serializer.data
        picture_url = data.get("picture")
        self.assertEqual(profile.picture.url, picture_url)

        profile.set_picture(None)

        serializer = ShortUserProfileSerializer(self.user)
        data = serializer.data
        picture_url = data.get("picture")
        self.assertEqual(picture_url, None)

        serializer = ShortProfileSerializer(profile)
        data = serializer.data
        username = data.get("username")
        self.assertEqual(username, self.user.username)
