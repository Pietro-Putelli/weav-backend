from django.db import models

from core.fields import UniqueNameFileField
from core.models import TimestampModel
from profiles.managers import (
    UserFriendManager,
    UserFriendRequestManager,
)


def get_default_settings():
    return {
        "language": "en",
        "notifications": {
            "all": False,
            "new_events": True,
            "new_venues": True,
            "chat_message": True,
            "moment_mention": True,
            "weekly_updates": True,
        },
    }


allow_blank = {"blank": True, "null": True}


def profile_picture_url(instance, *_):
    return f"users/{instance.user.uuid}/picture.png"


class UserProfile(models.Model):
    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="profile"
    )

    username = models.CharField(max_length=32, unique=True)
    bio = models.CharField(max_length=150, **allow_blank)

    link = models.URLField(max_length=256, **allow_blank)
    instagram = models.CharField(max_length=64, **allow_blank)

    picture = UniqueNameFileField(
        default=None, upload_to=profile_picture_url, **allow_blank
    )

    blocked_users = models.ManyToManyField(
        "profiles.UserProfile", related_name="blocked_profiles", blank=True
    )

    # To save user's app settings, such as notifications
    settings = models.JSONField(default=get_default_settings)

    # Latest user place id, to know its latest position
    latest_place_id = models.CharField(max_length=64, **allow_blank)

    def __str__(self):
        return f"{self.id} • {self.username}"

    def update_place_id(self, place_id):
        self.latest_place_id = place_id
        self.save()

    def set_picture(self, picture):
        self.picture.delete(save=True)
        self.picture = picture

        self.save()


class BusinessProfile(models.Model):
    user = models.OneToOneField(
        "users.User", on_delete=models.CASCADE, related_name="business_profile"
    )

    # If the user accepted terms and conditions
    accepted_terms = models.BooleanField(default=False)

    def accept_terms(self):
        self.accepted_terms = True
        self.save()

    def __str__(self):
        return self.user.name


class AbstractFriend(TimestampModel):
    user = models.ForeignKey(
        "profiles.UserProfile",
        related_name="_%(class)s_user_friend_request",
        on_delete=models.CASCADE,
    )

    friend = models.ForeignKey(
        "profiles.UserProfile",
        related_name="_%(class)s_friend_request",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True


class UserFriend(AbstractFriend):
    objects = UserFriendManager()


class UserFriendRequest(AbstractFriend):
    objects = UserFriendRequestManager()
