from django.db import models


class LoginChoices(models.TextChoices):
    EMAIL = "EMAIL", "email"
    GOOGLE = "google", "google"
    APPLE = "apple", "apple"
