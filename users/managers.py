import uuid

from django.db import models

from servicies.otp import get_otp_code
from django.contrib.auth.models import UserManager as DjangoUserManager


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
