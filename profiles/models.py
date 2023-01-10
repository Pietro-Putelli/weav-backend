from django.db import models

from core.fields import UniqueNameFileField
from core.models import TimestampModel
from profiles.managers import UserProfileManager, UserFriendManager, UserFriendRequestManager


def get_default_settings():
    return {
        "language": "en",
        "notifications": {
            "all": 0,
            "liked_venues": 1,
            "new_venues": 1,
            "chat_message": 1,
            "moment_tag": 1
        },
        "chance": {
            "enabled": 0,
            "today": 0,
            "event": 0,
            "sex": None,
            "interested": None
        }
    }


allow_blank = {"blank": True, "null": True}


def profile_picture_url(instance, *args):
    return f"{instance.user.id}/profile.picture.png"


class UserProfile(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="profile")

    name = models.CharField(max_length=32, default=None)
    bio = models.CharField(max_length=150, **allow_blank)

    link = models.URLField(max_length=256, **allow_blank)
    instagram = models.CharField(max_length=64, **allow_blank)

    picture = UniqueNameFileField(default=None, upload_to=profile_picture_url, **allow_blank)

    blocked_users = models.ManyToManyField(
        "users.User", related_name="blocked_users", blank=True
    )

    # To save user's app settings, such as notifications
    settings = models.JSONField(default=get_default_settings)

    public_key = models.CharField(max_length=64, default=None, **allow_blank)

    # Latest user place id, to know its latest position
    latest_place_id = models.CharField(max_length=64, **allow_blank)

    objects = UserProfileManager()

    def __str__(self):
        return f"{self.id} • {self.user.username}"

    def set_picture(self, picture):
        self.picture.delete(save=True)
        self.picture = picture

        self.save()

    def set_public_key(self, public_key):
        if public_key is not None:
            self.public_key = public_key
            self.save()


class AbstractFriend(TimestampModel):
    user = models.ForeignKey("users.User", related_name="_%(class)s_user_friend_request",
                             on_delete=models.CASCADE)
    friend = models.ForeignKey("users.User", related_name="_%(class)s_friend_request",
                               on_delete=models.CASCADE)

    class Meta:
        abstract = True


class UserFriend(AbstractFriend):
    objects = UserFriendManager()


class UserFriendRequest(AbstractFriend):
    objects = UserFriendRequestManager()
