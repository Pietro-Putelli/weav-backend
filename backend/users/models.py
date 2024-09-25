from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from core.fields import ShortUUIDField
from core.models import TimestampModel
from phonenumber_field.modelfields import PhoneNumberField
from services.otp import get_otp_code
from users.managers import AccessTokenManager, UserManager

no_blank = {"blank": False, "null": False}
allow_blank = {"blank": True, "null": True}


class LanguageChoices(models.TextChoices):
    ENGLISH = "en", "English"
    ITALIAN = "it", "Italian"


class User(AbstractBaseUser, PermissionsMixin, TimestampModel):
    uuid = ShortUUIDField()

    # Temporary use email instead of phone for users, because APIs are costly
    # and we don't want to waste them on users who are not going to use the app
    email = models.CharField(max_length=255, **allow_blank)

    phone = PhoneNumberField(unique=True, **allow_blank)
    name = models.CharField(max_length=32, **no_blank)
    language = models.TextField(default="en", choices=LanguageChoices.choices)

    # For Django Admin
    # email = models.CharField(max_length=255, **allow_blank)
    username = models.CharField(max_length=32, unique=True, **allow_blank)
    password = models.CharField(blank=True, null=True, max_length=128)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        indexes = [models.Index(fields=["uuid"])]

    def set_language(self, language):
        self.language = language
        self.save()

    def __str__(self):
        return f"{self.id} • {self.name}"


class AccessToken(models.Model):
    class Meta:
        unique_together = ("phone", "otp")

    phone = PhoneNumberField(unique=True, **no_blank)
    otp = models.CharField(max_length=6, default=get_otp_code)
    sid = models.CharField(max_length=34, blank=True, null=True)
    has_privilege = models.BooleanField(default=False)

    objects = AccessTokenManager()

    def delete(self, *args, **kwargs):
        if not self.has_privilege:
            super().delete(*args, **kwargs)

    def update_sid(self, sid):
        self.sid = sid
        self.save()

    def __str__(self):
        return f"{self.otp} • {self.phone}"
