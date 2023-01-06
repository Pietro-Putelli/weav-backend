import secrets

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.models import TimestampModel
from users.managers import UserManager, TokenCodeManager, AccessTokenManager

no_blank = {'blank': False, 'null': False}


class User(AbstractBaseUser, PermissionsMixin, TimestampModel):
    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField(**no_blank)

    password = models.CharField(blank=True, null=True, max_length=128)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=['id'])]

    def __str__(self):
        return f"{self.id} • {self.username}"


def generate_token():
    return secrets.token_hex()


def upload_qr_code(instance, _):
    return f"qr_codes/{instance.email}.png"


class AccessToken(models.Model):
    email = models.EmailField(**no_blank)
    value = models.CharField(max_length=64, default=generate_token)
    qrcode = models.ImageField(upload_to=upload_qr_code, default=None)

    objects = AccessTokenManager()

    class Meta:
        unique_together = ('email', 'value')

    def __str__(self):
        return f"{self.id} • {self.email}"


class TokenCode(models.Model):
    email = models.EmailField(**no_blank)
    value = models.CharField(max_length=64)
    code = models.CharField(max_length=5)

    objects = TokenCodeManager()
