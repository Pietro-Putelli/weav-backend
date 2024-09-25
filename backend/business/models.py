import binascii
import os

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models.query_utils import Q
from core.fields import UniqueNameFileField

from business.managers import BusinessManager
from core.fields import ShortUUIDField
from core.models import TimestampModel
from phonenumber_field.modelfields import PhoneNumberField

allow_blank = {"blank": True, "null": True}


def get_default_settings():
    return {"notifications": {"all": False, "new_insight": True, "chat_message": True}}


def business_source_path(instance, filename):
    return f"users/{instance.owner.user.uuid}/business/{instance.uuid}/{filename}"


class Business(TimestampModel):
    uuid = ShortUUIDField()

    owner = models.ForeignKey(
        "profiles.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="business_owner",
    )

    name = models.CharField(max_length=32, default=None)

    category = models.ForeignKey(
        "shared.BusinessCategory",
        on_delete=models.NOT_PROVIDED,
        related_name="business_main_category",
        **allow_blank,
    )

    categories = models.ManyToManyField(
        "shared.BusinessCategory", blank=True, related_name="business_categories"
    )

    amenities = models.ManyToManyField(
        "shared.Amenity", blank=True, related_name="business_amenities"
    )

    location = models.OneToOneField(
        "shared.Location",
        related_name="%(app_label)s_%(" "class)s_likes",
        db_index=False,
        on_delete=models.CASCADE,
        **allow_blank,
    )

    phone = PhoneNumberField(default=None, **allow_blank, validators=[])

    timetable = models.OneToOneField(
        "business.BusinessTimetable", on_delete=models.CASCADE, **allow_blank
    )

    description = models.TextField(max_length=256, **allow_blank)

    price_target = models.IntegerField(default=2, **allow_blank)

    menu_url = models.TextField(**allow_blank)
    ticket_url = models.TextField(**allow_blank)
    web_url = models.TextField(**allow_blank)
    instagram = models.CharField(max_length=64, **allow_blank)
    nearby_info = models.CharField(max_length=64, **allow_blank)

    extra_data = models.JSONField(**allow_blank)

    allow_chat = models.BooleanField(default=True)

    is_approved = models.BooleanField(default=False)

    cover_source = UniqueNameFileField(blank=False, upload_to=business_source_path)

    likes = models.ManyToManyField("profiles.UserProfile", blank=True)

    delivery_options = ArrayField(models.CharField(max_length=255), **allow_blank)

    # Business personal settings
    settings = models.JSONField(default=get_default_settings, **allow_blank)

    reposts_count = models.IntegerField(default=0)

    objects = BusinessManager()

    def add_repost(self):
        self.reposts_count += 1
        self.save()

    def sub_repost(self):
        self.reposts_count -= 1
        self.save()

    class Meta:
        indexes = [
            models.Index(
                fields=["id"],
                condition=Q(is_approved=True),
                name="%(app_label)s_id_part_ix",
            ),
            models.Index(
                fields=["location"],
                condition=Q(is_approved=True),
                name="%(app_label)s_location_part_ix",
            ),
        ]

    # METHODS

    def update_cover(self, cover):
        self.cover_source = cover
        self.save()

    def update_settings(self, settings):
        self.settings = settings
        self.save()

    def __str__(self):
        return f"{self.id} • {self.name}"


def generate_key():
    return binascii.hexlify(os.urandom(20)).decode()


class BusinessToken(models.Model):
    business = models.OneToOneField("Business", on_delete=models.CASCADE)
    key = models.CharField(primary_key=True, default=generate_key, max_length=40)


class BusinessTimetable(models.Model):
    mon = ArrayField(models.DateTimeField(), **allow_blank)
    tue = ArrayField(models.DateTimeField(), **allow_blank)
    wed = ArrayField(models.DateTimeField(), **allow_blank)
    thu = ArrayField(models.DateTimeField(), **allow_blank)
    fri = ArrayField(models.DateTimeField(), **allow_blank)
    sat = ArrayField(models.DateTimeField(), **allow_blank)
    sun = ArrayField(models.DateTimeField(), **allow_blank)

    def update(self, timetable):
        for key, value in timetable.items():
            setattr(self, key, value)
            self.save()


class BusinessHighlight(models.Model):
    business = models.ForeignKey("Business", on_delete=models.CASCADE)
    title = models.CharField(max_length=32)
    content = models.TextField(max_length=128)
