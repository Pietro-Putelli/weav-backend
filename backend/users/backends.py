from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from users.models import User


class UserBackend(BaseBackend):
    def authenticate(self, request=None, username=None, password=None):
        try:
            user = User.objects.get(Q(username=username) | Q(phone=username))

            password_valid = user.check_password(password)

            if password_valid:
                return user
            return None
        except ObjectDoesNotExist:
            return None
