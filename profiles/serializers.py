from rest_framework import serializers

from moments.models import UserMoment
from profiles.models import UserProfile
from profiles.utils import get_friendship_state
from shared.serializers import PhoneSerializer

PROFILE_FIELDS = ("name", "bio", "link", "instagram", "friend_state")


class UserProfileSerializer(serializers.ModelSerializer):
    phone = PhoneSerializer()
    friend_state = serializers.SerializerMethodField()
    has_moments = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = PROFILE_FIELDS + ("has_moments",)

    def get_friend_state(self, profile):
        user = self.context.get("user")
        return get_friendship_state(user, profile.user)

    def get_has_moments(self, profile):
        return UserMoment.objects.filter(user=profile.user).exists()


class UserChatProfileSerializer(UserProfileSerializer):
    class Meta(UserProfileSerializer.Meta):
        fields = PROFILE_FIELDS + ("has_moments", "public_key",)


class ShortUserProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    id = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    def get_id(self, user):
        return user.uuid

    def get_picture(self, user):
        picture = user.profile.picture

        try:
            picture_url = picture.url
            return picture_url
        except ValueError:
            return None


class ShortProfileSerializer(serializers.Serializer):
    uuid = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    picture = serializers.ImageField()

    def get_id(self, profile):
        return profile.user.uuid

    def get_username(self, profile):
        return profile.user.username


class ShortUserProfileChatSerializer(ShortUserProfileSerializer):
    public_key = serializers.SerializerMethodField()

    def get_public_key(self, user):
        return user.profile.public_key


class UserFriendRequestSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    def get_id(self, profile):
        return profile.user.uuid

    def get_user(self, profile):
        return ShortUserProfileSerializer(profile.user).data
