from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models

from devices.models import Device
from profiles.models import UserProfile
from services.otp import get_otp_code


class AccessTokenManager(models.Manager):
    def create_or_update(self, phone):
        token, created = self.get_or_create(phone=phone)

        if not created:
            if token.has_privilege:
                return token

            token.otp = get_otp_code()

        token.save()

        return token


class UserManager(DjangoUserManager):
    def create_user(self, **kwargs):
        username = kwargs.pop("username", None)
        picture = kwargs.pop("picture", None)
        name = kwargs.pop("name", None)
        os_type = kwargs.pop("os_type")

        if name is None:
            name = username

        user = self.model(name=name, **kwargs)
        user.save()

        if username is not None:
            UserProfile.objects.create(user=user, username=username, picture=picture)

        Device.objects.update_or_create(user=user, os_type=os_type)

        return user

    def get_only_active(self):
        return self.get_queryset().filter(is_active=True)
