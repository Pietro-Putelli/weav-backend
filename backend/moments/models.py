import uuid

from django.core.validators import URLValidator
from django.db import models
from django.db.models import CASCADE

from core.fields import TextField, ShortUUIDField
from core.fields import UniqueNameFileField
from core.models import TimestampModel
from moments.managers import EventMomentManager, UserMomentManager
from services.utils import get_abstract_related_name

allow_blank = {"blank": True, "null": True}
many_to_many_params = {"default": None, "blank": True}


def user_moment_source_path(instance, _):
    filename = uuid.uuid1()
    return f"users/{instance.user.user.uuid}/moments/{filename}.png"


class UserMoment(TimestampModel):
    uuid = ShortUUIDField()

    user = models.ForeignKey(
        "profiles.UserProfile", related_name="user_moment", on_delete=CASCADE
    )

    is_anonymous = models.BooleanField(default=False)

    location = models.OneToOneField(
        "shared.Location", related_name="user_moment_location", on_delete=CASCADE
    )

    content = TextField(max_length=300, **allow_blank)

    source = UniqueNameFileField(upload_to=user_moment_source_path, blank=True)

    # IMAGE_HEIGHT / IMAGE_WIDTH
    ratio = models.FloatField(null=True, blank=True)

    event = models.ForeignKey("moments.EventMoment", on_delete=CASCADE, **allow_blank)

    end_at = models.DateTimeField(default=None)

    participants = models.ManyToManyField(
        "profiles.UserProfile", related_name="participants", **many_to_many_params
    )

    replied_by = models.ManyToManyField(
        "profiles.UserProfile", related_name="replied_by", **many_to_many_params
    )

    business_tag = models.ForeignKey(
        "business.Business",
        related_name=get_abstract_related_name("business_tag"),
        on_delete=CASCADE,
        **allow_blank,
    )

    url_tag = models.TextField(
        max_length=512, validators=[URLValidator()], default=None, **allow_blank
    )

    location_tag = models.ForeignKey(
        "shared.Location",
        related_name=get_abstract_related_name("location_tag"),
        on_delete=CASCADE,
        **allow_blank,
    )

    objects = UserMomentManager()

    @property
    def source_url(self):
        if self.source:
            return self.source.url
        return None

    def set_source(self, source):
        self.source = source
        self.save()

    def __str__(self):
        return f"{self.uuid} – {self.content}"


def event_moment_source_path(instance, filename):
    return f"users/{instance.business.owner.user.uuid}/events/{filename}"


class EventMoment(TimestampModel):
    uuid = ShortUUIDField()

    business = models.ForeignKey(
        "business.Business",
        related_name="business_moment",
        db_index=False,
        on_delete=CASCADE,
    )

    cover = UniqueNameFileField(upload_to=event_moment_source_path)
    ratio = models.FloatField(null=True, blank=True)

    date = models.DateField(default=None, **allow_blank)
    time = models.TimeField(default=None)
    end_time = models.TimeField(default=None)

    # Ex. every Monday event
    periodic_day = models.IntegerField(default=None, **allow_blank)

    title = models.CharField(max_length=32, default=None)

    participants = models.ManyToManyField("profiles.UserProfile", blank=True)

    guests = models.CharField(max_length=64, **allow_blank)
    price = models.CharField(max_length=64, **allow_blank)
    instagram = models.CharField(max_length=64, **allow_blank)
    website = models.CharField(max_length=64, **allow_blank)
    ticket = models.TextField(**allow_blank)
    description = models.TextField(max_length=256, default=None, **allow_blank)

    location = models.ForeignKey("shared.Location", on_delete=CASCADE, **allow_blank)

    reposts_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)

    has_activity = models.BooleanField(default=False)

    objects = EventMomentManager()

    def update_location(self, location):
        self.location = location
        self.save()

    def add_repost(self):
        self.reposts_count += 1
        self.save()

    def sub_repost(self):
        self.reposts_count -= 1
        self.save()

    def add_share(self):
        self.shares_count += 1
        self.save()

    class Meta:
        indexes = [models.Index(fields=["date", "business"])]

    def __str__(self):
        return f"{self.id} • {self.title}"
