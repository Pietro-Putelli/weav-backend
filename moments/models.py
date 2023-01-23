import uuid

from django.core.validators import URLValidator
from django.db import models
from django.db.models import CASCADE

from core.fields import TextField, ShortUUIDField
from core.fields import UniqueNameFileField
from core.models import TimestampModel
from moments.managers import EventMomentManager, EventMomentSliceManager, UserMomentManager
from servicies.utils import get_abstract_related_name

allow_blank = {"blank": True, "null": True}


class AbstractTagsModel(models.Model):
    users_tag = models.ManyToManyField("users.User", blank=True)

    business_tag = models.ForeignKey(
        "business.Business", related_name=get_abstract_related_name("business_tag"),
        on_delete=CASCADE, **allow_blank)

    url_tag = models.TextField(max_length=512, validators=[
        URLValidator()], default=None, **allow_blank)

    location_tag = models.ForeignKey(
        "shared.Location", related_name=get_abstract_related_name("location_tag"),
        on_delete=CASCADE, **allow_blank)

    class Meta:
        abstract = True


def user_moment_source_path(instance, _):
    filename = uuid.uuid1()
    return f"{instance.user.id}/moments/{filename}.png"


class UserMoment(TimestampModel, AbstractTagsModel):
    uuid = ShortUUIDField()

    user = models.ForeignKey(
        "users.User", related_name="user_moment", on_delete=CASCADE)

    location = models.OneToOneField(
        "shared.Location", related_name="user_moment_location", on_delete=CASCADE)

    content = TextField(max_length=300, **allow_blank)

    source = UniqueNameFileField(upload_to=user_moment_source_path, blank=True)

    # IMAGE_HEIGHT / IMAGE_WIDTH
    ratio = models.FloatField(null=True, blank=True)

    event = models.ForeignKey("moments.EventMomentSlice", on_delete=CASCADE,
                              **allow_blank)

    end_at = models.DateTimeField(default=None)

    objects = UserMomentManager()

    def __str__(self):
        return f"{self.user.id} – {self.content}"


def event_moment_source_path(instance, filename):
    return f"{instance.moment.business.owner.id}/event_moments/{filename}"


class EventMoment(TimestampModel):
    uuid = ShortUUIDField()

    business = models.ForeignKey(
        "business.Business", related_name="business_moment", db_index=False, on_delete=CASCADE)

    date = models.DateField(default=None)
    time = models.TimeField(default=None)
    title = models.CharField(max_length=32, default=None)

    participants = models.ManyToManyField("users.User", blank=True)

    guests = models.CharField(max_length=64, **allow_blank)
    price = models.CharField(max_length=64, **allow_blank)
    instagram = models.CharField(max_length=64, **allow_blank)
    website = models.CharField(max_length=64, **allow_blank)
    ticket = models.TextField(**allow_blank)
    description = models.TextField(max_length=256, default=None, **allow_blank)

    location = models.ForeignKey("shared.Location", on_delete=CASCADE, **allow_blank)

    reposts_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)

    objects = EventMomentManager()

    def update_location(self, location):
        self.location = location
        self.save()

    def add_repost(self):
        self.reposts_count += 1
        self.save()

    def add_share(self):
        self.shares_count += 1
        self.save()

    class Meta:
        indexes = [models.Index(fields=["date", "business"])]

    def __str__(self):
        return f"{self.id} • {self.business.id}"


class EventMomentSlice(TimestampModel):
    moment = models.ForeignKey(
        "EventMoment", related_name="event_moment_slice", on_delete=CASCADE)
    source = UniqueNameFileField(upload_to=event_moment_source_path)

    objects = EventMomentSliceManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.moment.business.id} - {self.moment.id}"
