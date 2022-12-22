from django.test import TestCase
from datetime import datetime

from profiles.models import UserProfile
from users.models import User

USERS_COUNT = 10000


class UserTestCase(TestCase):
    def setUp(self):
        start_time = datetime.now()
        users = []
        profiles = []
        batch_size = 500
        for i in range(USERS_COUNT):
            user = User()
            user.username = str(i)
            user.password = str(i)
            users.append(user)

            profile = UserProfile(user=user, name=str(i))
            profiles.append(profile)

        User.objects.bulk_create(users, batch_size)
        UserProfile.objects.bulk_create(profiles, batch_size)

        end_time = datetime.now()
        print(f" Created in {end_time - start_time}")

    def test_profile_lookup(self):
        user_qs = User.objects.filter(id=9898)
        user = user_qs.first()

        profile_qs = UserProfile.objects.filter(user=user)

        print("USER = ", user_qs.explain())
        print("PROFILE = ", profile_qs.explain())
