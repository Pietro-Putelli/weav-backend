from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from core.models import TimestampModel
from users.managers import TokenCodeManager, UserManager


class User(AbstractBaseUser, PermissionsMixin, TimestampModel):
    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=['id'])]

    def __str__(self):
        return f"{self.id} • {self.username}"


class TokenCode(models.Model):
    username = models.CharField(max_length=256)  # phone or email
    value = models.CharField(max_length=64)
    code = models.CharField(max_length=5)

    objects = TokenCodeManager()

    def __str__(self):
        return f"{self.username} • {self.value} • {self.code}"
