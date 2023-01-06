import uuid
import secrets

from django.db import models

from profiles.models import UserProfile
from servicies.otp import get_otp_code
from django.contrib.auth.models import UserManager as DjangoUserManager

from users.utils import generate_qrcode


class AccessTokenManager(models.Manager):
    def create_or_update(self, email):
        token, created = self.get_or_create(email=email)

        if not created:
            token_value = secrets.token_hex()
            token.value = token_value
            token.qrcode = generate_qrcode(token_value)
        else:
            token.qrcode = generate_qrcode(token.value)

        token.save()

        return token


class TokenCodeManager(models.Manager):

    def update_or_create(self, username):
        value = uuid.uuid4()
        code = get_otp_code()

        queryset = self.get_queryset().filter(username=username)

        if queryset.exists():
            queryset.update(code=code)
            return queryset.first()

        token = self.create(username=username, value=value, code=code)
        return token

    def delete_for(self, user):
        token = self.get_queryset().filter(username=user.username).first()

        if token is not None:
            token.delete()


class UserManager(DjangoUserManager):
    def get_or_none(self, email):
        try:
            return self.get_queryset().get(email=email)
        except self.model.DoesNotExist:
            return None

    def create_user(self, **kwargs):
        name = kwargs.pop('name')

        user = super().create_user(**kwargs)
        UserProfile.objects.create(user=user, name=name)

        return user
