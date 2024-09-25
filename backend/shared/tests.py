from phonenumber_field import PhoneNumber
from rest_framework.test import APITestCase, APIClient
from django.contrib.gis.geos.point import Point

from core.test_utilis import get_mocked_file
from core.fields import UniqueNameFileField
from shared.models import Location
from shared.serializers import CoordinateSerializer, CreateLocationSerializer, PhoneSerializer, \
    CreatePhoneSerializer

LIST_COORDINATE = [11.86515091022377, 45.41636402211313]
COORDINATE = {"longitude": 11.86515091022377, "latitude": 45.41636402211313}

LOCATION = {
    "address": "Baker Street 221/B",
    "coordinate": COORDINATE,
    "city": "Padova",
    "country": "IT",
    "place_id": "this_is_a_place_id"
}

PHONE_NUMBER = {
    "country_code": "39",
    "national_number": "3347676270"
}


class ManagerAPITestCase(APITestCase):
    def test_location(self):
        location = Location.objects.create(**LOCATION)

        self.assertTrue(location.coordinate.x, LIST_COORDINATE[0])
        self.assertTrue(location.coordinate.y, LIST_COORDINATE[1])


class SerializerAPITestCase(APITestCase):
    def test_coordinate(self):
        coordinate = Point(LIST_COORDINATE)

        serializer = CoordinateSerializer(coordinate)
        data = serializer.data

        longitude = data.get("longitude")
        latitude = data.get("latitude")

        self.assertEqual(coordinate.x, longitude)
        self.assertEqual(coordinate.y, latitude)

    def test_create_location(self):
        serializer = CreateLocationSerializer(data=LOCATION)
        self.assertTrue(serializer.is_valid())

        data = {"address": LOCATION["address"], "coordinate": {}}
        serializer = CreateLocationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_phone(self):
        phone_number = PhoneNumber(**PHONE_NUMBER)

        serializer = PhoneSerializer(phone_number)
        data = serializer.data

        prefix = data.get("prefix")
        number = data.get("number")

        self.assertEqual(PHONE_NUMBER['country_code'], prefix)
        self.assertEqual(PHONE_NUMBER["national_number"], number)

    def test_create_phone(self):
        data = {
            "code": PHONE_NUMBER["country_code"],
            "number": PHONE_NUMBER["national_number"]
        }

        serializer = CreatePhoneSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class FieldAPITestCase(APITestCase):
    def test_file_field(self):
        file_name = "source.png"
        source = get_mocked_file(file_name)
        field = UniqueNameFileField(upload_to="")

        unique_name = field.generate_filename(source, file_name)
        self.assertIsNotNone(unique_name, None)
