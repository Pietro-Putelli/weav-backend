from datetime import datetime

from django.db.models.signals import post_save
from django.test import TestCase

from business.models import Business
from core.test_utilis import get_mocked_file
from moments.models import UserMoment, EventMoment, EventMomentSlice
from servicies.date import date_from
from shared.models import Location, BusinessCategory
from users.models import User

ENTRIES_COUNT = 10000

COORDINATE = [11.86515091022377, 45.41636402211313]

PADUA_PLACE_ID = "place.39233648"

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


def print_duration(start_date):
    end_date = datetime.now()

    delta = abs(start_date - end_date).total_seconds()
    print(f"END IN = {delta} s")


class UserMomentTestCase(TestCase):
    def setUp(self):
        users = []

        for i in range(0, ENTRIES_COUNT):
            user = User()
            user.username = str(i)
            user.password = str(i)
            users.append(user)

        User.objects.bulk_create(users)

        moments = []

        for i in range(0, ENTRIES_COUNT):
            location = Location.objects.create(coordinate=COORDINATE)

            if i % int(ENTRIES_COUNT / 20) == 0:
                location.place_id = PADUA_PLACE_ID
                location.save()

            moment = UserMoment(user=users[i], location=location, content=str(i))
            moments.append(moment)

        UserMoment.objects.bulk_create(moments)

    # def test_get_moments_by_user(self):
    #     start_date = datetime.now()
    #     user = User.objects.filter(id=886).first()
    #
    #     queryset = UserMoment.objects.filter(user=user)
    #
    #     print_duration(start_date)
    #     print("[TEST-1]", queryset.explain())

    def test_get_moments_by_date(self):
        start_date = datetime.now()

        qs = UserMoment.objects.filter(created_at__gte=date_from(1),
                                       location__place_id=PADUA_PLACE_ID)

        print_duration(start_date)
        print("[TEST-2]", qs.explain())


class EventMomentTestCase(TestCase):
    def setUp(self):
        users = []
        profiles = []

        for i in range(0, ENTRIES_COUNT):
            user = User()
            user.username = str(i)
            user.password = str(i)
            users.append(user)

            profile = BusinessProfile(user=user)
            profiles.append(profile)

        User.objects.bulk_create(users)
        BusinessProfile.objects.bulk_create(profiles)

        moments = []
        slices = []

        for i in range(0, ENTRIES_COUNT):
            location = Location.objects.create(coordinate=COORDINATE)

            if i % int(ENTRIES_COUNT / 30) == 0:
                location.place_id = PADUA_PLACE_ID
                location.save()

            source = get_mocked_file("source.png")

            category = BusinessCategory.objects.create(title="Vero", key=12)

            business = Business.objects.create(profile=profiles[i],
                                               category=category,
                                               location=location,
                                               cover_source=source,
                                               **BUSINESS)

            moment = EventMoment.objects.create(business=business)
            moments.append(moment)

            slice = EventMomentSlice.objects.create(moment=moment, source=source)
            slices.append(slice)

        self.one_moment = moments[0]

    def test_get_moments(self):
        start_date = datetime.now()
        qs = EventMoment.objects.filter(created_at=date_from(1),
                                        business__location__place_id=PADUA_PLACE_ID)

        print_duration(start_date)
        print("[TEST-1]", qs.explain())
