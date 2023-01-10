from datetime import datetime

from django.db.models.signals import post_save
from django.test import TestCase

from business.models import Business
from business.signals import rename_business_dir
from core.test_utilis import get_mocked_file
from profiles.models import BusinessProfile
from shared.models import Location, BusinessCategory
from users.models import User

ENTRIES_COUNT = 1000

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
}


def print_duration(start_date):
    end_date = datetime.now()

    delta = abs(start_date - end_date).total_seconds()
    print(f"END IN = {delta} s")


class BusinessTestCase(TestCase):
    def setUp(self):
        users = []
        profiles = []
        venues = []

        for i in range(ENTRIES_COUNT):
            user = User()
            user.username = str(i)
            user.password = str(i)
            users.append(user)

            profile = BusinessProfile(user=user)
            profiles.append(profile)

        User.objects.bulk_create(users)
        BusinessProfile.objects.bulk_create(profiles)

        post_save.disconnect(rename_business_dir, sender=Business)

        for i in range(0, ENTRIES_COUNT):
            location = Location.objects.create(coordinate=COORDINATE)

            if i % 3 == 0:
                location.place_id = PADUA_PLACE_ID
                location.save()

            source = get_mocked_file("source.png")

            category = BusinessCategory.objects.create(title="Vero", key=12)

            is_approved = i % 4 != 0

            business = Business(profile=profiles[i],
                                category=category,
                                location=location,
                                cover_source=source,
                                is_approved=is_approved,
                                **BUSINESS)
            venues.append(business)

        Business.objects.bulk_create(venues)

    def test_get_business(self):
        start = datetime.now()
        qs = Business.objects.filter(is_approved=True, location__place_id=PADUA_PLACE_ID)

        print_duration(start)
        print("[test-1]", qs.explain())
