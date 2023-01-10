from django.db.models import signals
from rest_framework.test import APITestCase, APIClient

from users.models import User


class UserMomentTestCase(APITestCase):
    def setUp(self):
        signals.post_save.receivers = []

        self.user = User.objects.create(username="pietro", password="12345678",
                                        email="pietro@gmail.com")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
