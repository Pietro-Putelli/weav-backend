from rest_framework import serializers

from moments.models import UserMoment
from profiles.models import UserProfile
from profiles.utils import get_friendship_state
from shared.serializers import PhoneSerializer

PROFILE_FIELDS = ("username", "bio", "link", "instagram", "friend_state")


class UserProfileSerializer(serializers.ModelSerializer):
    phone = PhoneSerializer()
    friend_state = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = PROFILE_FIELDS

    def get_friend_state(self, profile):
        user = self.context.get("user")
        return get_friendship_state(user, profile)


class ShortUserProfileSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    username = serializers.CharField()
    picture = serializers.ImageField()

    def get_id(self, profile):
        return profile.user.uuid


class LongUserProfileSerializer(UserProfileSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_id(self, profile):
        return profile.user.uuid

    def get_name(self, profile):
        return profile.user.name

    class Meta(UserProfileSerializer.Meta):
        fields = PROFILE_FIELDS + (
            "id",
            "name",
            "picture",
        )


class VeryShortUserProfileSerializer(ShortUserProfileSerializer):
    username = None
    id = None


class UserFriendRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user = serializers.SerializerMethodField()

    def get_user(self, request):
        return ShortUserProfileSerializer(request.user).data
