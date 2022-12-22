import json

from django.db.models.signals import post_save
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from business.models import Business
from business.signals import rename_business_dir
from core.test_utilis import get_mocked_file
from moments.models import UserMoment, EventMoment, EventMomentSlice
from moments.serializers import UserMomentSerializer, EventMomentSerializer, \
    EventMomentSliceSerializer, CreateUserMomentSerializer, MomentTagsSerializer
from moments.tag_serializers import UrlTagSerializer, LocationTagSerializer
from profiles.models import UserProfile, BusinessProfile
from servicies.choices import SourceChoices
from shared.models import Location
from users.models import User

USER = {
    "username": "pietro.putelli",
    "password": "sticazzi"
}
USER_PROFILE_NAME = "Pietro Putelli"

GUEST_USER = {
    "username": "steve.jobs",
    "password": "12345"
}
USER_GUEST_NAME = "Steve Jobs"

COORDINATE = [11.86515091022377, 45.41636402211313]

TAGS = {
    "url": "https://www.isolaelba.com",
}

BUSINESS = {
    "type": "bar",
    "name": "The Aviators Club",
    "phone": "+393347676270",
    "timetable": {"": ""},
    "description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus non urna "
                   "posuere, placerat massa vel, auctor neque.",
    "price_target": 4,
    "is_approved": True
}

USER_MOMENT_CREATE = {
    "content": "hey",
    "source_type": SourceChoices.PHOTO,
    "location": {
        "coordinate": {
            "longitude": COORDINATE[0],
            "latitude": COORDINATE[1]
        }
    },
    "users_tag": [GUEST_USER["username"]]
}

GET_MOMENT_PARAMS = {
    "place_id": "",
    "search_type": "city",
    "offset": 0,
    "coordinate": COORDINATE
}

EVENT_MOMENT_CREATE = {
    "data": json.dumps({
        "business_id": 1,
        "slices_count": 1
    }),
}

EVENT_MOMENT_SLICE_FILE_PATH = ""


class GeneralAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(**USER)
        UserProfile.objects.create(user=user, name=USER_PROFILE_NAME)

        guest_user = User.objects.create_user(**GUEST_USER)
        UserProfile.objects.create(user=guest_user, name=USER_GUEST_NAME)

        location = Location.objects.create(coordinate=COORDINATE)
        source = get_mocked_file("source.png")

        user_moment = UserMoment.objects.create(user=user, location=location, source=source,
                                                source_type="photo",
                                                url_tag=TAGS["url"])

        user_moment.users_tag.add(guest_user)

        post_save.disconnect(rename_business_dir, sender=Business)

        business_profile = BusinessProfile.objects.create(user=user)

        business = Business.objects.create(profile=business_profile,
                                           location=location,
                                           cover_source=source,
                                           **BUSINESS)

        event_moment = EventMoment.objects.create(business=business)

        cls.event_moment_slice = EventMomentSlice.objects.create(moment=event_moment,
                                                                 source=source,
                                                                 source_type="photo")

        cls.user = user
        cls.guest_user = guest_user
        cls.user_moment = user_moment
        cls.event_moment = event_moment

        cls.location = location
        cls.business = business

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)


class SignalAPITestCase(GeneralAPITestCase):
    def test_connection(self):
        slice = EventMomentSlice.objects.first()

        self.assertIsNotNone(slice)


class UserMomentTestCase(GeneralAPITestCase):
    def test_post_moment(self):
        uri = reverse("user")

        source = get_mocked_file("source.png")

        data = {
            "data": json.dumps(USER_MOMENT_CREATE),
            "source": source
        }

        response = self.client.post(uri, data)
        self.assertEqual(response.status_code, 200)

        error_data = {"data": "{}"}

        response = self.client.post(uri, error_data)
        self.assertEqual(response.status_code, 400)

    def test_get_moments(self):
        uri = reverse("get_user_moments")
        response = self.client.post(uri, GET_MOMENT_PARAMS)

        self.assertEqual(response.status_code, 200)


class EventMomentTestCase(GeneralAPITestCase):
    def test_post(self):
        uri = reverse("event")

        source = get_mocked_file("source.png")

        data = {
            **EVENT_MOMENT_CREATE,
            "source_0": source,
            "data_0": json.dumps({
                "content": "",
                "source_type": SourceChoices.PHOTO
            })
        }

        response = self.client.post(uri, data)
        self.assertEqual(response.status_code, HTTP_200_OK)

        error_data = {"data": "{}"}

        response = self.client.post(uri, error_data)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

        error_data = {**EVENT_MOMENT_CREATE, "data_0": None}

        response = self.client.post(uri, error_data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_get(self):
        uri = reverse("get_event_moments")
        response = self.client.post(uri, GET_MOMENT_PARAMS)

        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_delete(self):
        uri = reverse("event")

        param = {"moment_id": self.event_moment.id}
        response = self.client.delete(uri, param)

        self.assertEqual(response.status_code, HTTP_200_OK)

        response = self.client.delete(uri, {})
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)


class SerializerTestCase(GeneralAPITestCase):
    def test_moment_tag(self):
        serializer = MomentTagsSerializer(self.user_moment)

        data = serializer.data
        users_tag = data.get("users_tag")
        serialized_user_id = users_tag[0].get("id")

        user = self.user_moment.users_tag.all()[0]

        self.assertEqual(serialized_user_id, f"user.{user.id}")

    def test_user_moment(self):
        serializer = UserMomentSerializer(self.user_moment)

        data = serializer.data
        moment_id = data.get("id")

        self.assertEqual(f"moment.user.{self.user_moment.id}", moment_id)

    def test_event_moment(self):
        serializer = EventMomentSerializer(self.event_moment)

        data = serializer.data
        moment_id = data.get("id")

        self.assertEqual(f"moment.event.{self.event_moment.id}", moment_id)

    def test_event_moment_slice(self):
        serializer = EventMomentSliceSerializer(self.event_moment_slice)

        data = serializer.data
        slice_id = data.get("id")

        self.assertEqual(f"slice.{self.event_moment_slice.id}", slice_id)

    def test_create_user_moment(self):
        serializer = CreateUserMomentSerializer(data=USER_MOMENT_CREATE)

        self.assertTrue(serializer.is_valid())

        moment = serializer.save(user=self.user)

        self.assertSequenceEqual(moment.location.coordinate, COORDINATE)

        users_tag = serializer.validated_data.get("users_tag")
        self.assertSequenceEqual(users_tag, USER_MOMENT_CREATE["users_tag"])

        users = User.objects.filter(username__in=users_tag)

        self.assertQuerysetEqual(users, moment.users_tag.all())


class TagSerializerTestCase(GeneralAPITestCase):
    def test_url(self):
        serializer = UrlTagSerializer(self.user_moment.url_tag)

        data = serializer.data
        value = data.get("value")

        self.assertEqual(value, TAGS["url"])

    def test_location(self):
        serializer = LocationTagSerializer(self.location)

        data = serializer.data
        coordinate = data.get("coordinate")

        longitude = coordinate.get("longitude")
        latitude = coordinate.get("latitude")

        self.assertEqual(longitude, COORDINATE[0])
        self.assertEqual(latitude, COORDINATE[1])
