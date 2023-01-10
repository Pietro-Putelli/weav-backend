from django.db import models


class RepostAndShareChoices(models.TextChoices):
    MOMENT = "MOMENT", "moment"
    BUSINESS = "BUSINESS", "business"
