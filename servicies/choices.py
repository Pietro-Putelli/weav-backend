from django.db import models


class SourceChoices(models.TextChoices):
    PHOTO = "photo", "photo"
    VIDEO = "video", "video"


class LoginChoices(models.TextChoices):
    EMAIL = "EMAIL", "email"
    GOOGLE = "google", "google"
