from rest_framework.test import APITestCase, APIClient
from django.db.models import signals
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

USER_REGISTRATION = {
    "username": "pietro_putelli",
    "email": "pietroputelli80@gmail.com",
    "name": "Pietro Putelli"
}


class UserTestCase(APITestCase):
    def setUp(self):
        signals.post_save.receivers = []

        self.client = APIClient()

    def test_user_registration(self):
        url = reverse("register")

        response = self.client.post(url, USER_REGISTRATION)
        self.assertEqual(response.status_code, HTTP_200_OK)
