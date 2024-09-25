from django.db import models
from core.fields import TextField, ShortUUIDField
from core.models import TimestampModel

allow_blank = {"blank": True, "null": True}


class Spot(TimestampModel):
    uuid = ShortUUIDField()

    profile = models.ForeignKey('profiles.UserProfile', on_delete=models.CASCADE, **allow_blank)
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE)

    is_anonymous = models.BooleanField(default=True)

    content = TextField(max_length=300)

    replies = models.ManyToManyField('profiles.UserProfile', related_name='replies', blank=True)

    def __str__(self):
        return f"{self.id} • {self.business.name}"
