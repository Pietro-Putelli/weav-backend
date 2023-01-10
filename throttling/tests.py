from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient


class ThrottlingTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_unauthenticated_throttle(self):
        url = reverse('login')

        for _ in range(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 429)
