from business.models import Business
from business.serializers import MyBusinessSerializer
from profiles.models import UserProfile
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from shared.serializers import CreatePhoneSerializer, PhoneSerializer
from users.models import User


class UserSignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField()
    phone = CreatePhoneSerializer()
    language = serializers.CharField()
    os_type = serializers.CharField()

    def save(self, picture):
        return User.objects.create_user(**self.validated_data, picture=picture)


class SocialUserSignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField(required=False, allow_null=True)
    email = serializers.CharField()
    language = serializers.CharField()
    os_type = serializers.CharField()

    def save(self, picture):
        return User.objects.create_user(**self.validated_data, picture=picture)


class UserLoginSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    auth_token = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    has_business = serializers.SerializerMethodField()
    has_multiple_businesses = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "name",
            "bio",
            "instagram",
            "link",
            "picture",
            "auth_token",
            "username",
            "settings",
            "language",
            "has_business",
            "has_multiple_businesses",
        )

    def get_id(self, profile):
        return profile.user.uuid

    def get_auth_token(self, profile):
        return Token.objects.get(user=profile.user).key

    def get_name(self, profile):
        return profile.user.name

    def get_language(self, profile):
        return profile.user.language

    def get_has_business(self, profile):
        business = Business.objects.filter(owner__user=profile.user).first()
        return business is not None

    def get_has_multiple_businesses(self, profile):
        businesses = Business.objects.filter(owner__user=profile.user)
        return businesses.count() > 1


# When the user logs in after re-installing the app


class UserLoginWithTokenSerializer(UserLoginSerializer):
    phone = serializers.SerializerMethodField()
    has_multiple_businesses = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = UserLoginSerializer.Meta.fields + ("phone", "has_multiple_businesses")

    def get_phone(self, profile):
        phone = PhoneSerializer(profile.user.phone)
        return phone.data

    def get_has_multiple_businesses(self, profile):
        businesses = Business.objects.filter(owner__user=profile.user)
        return businesses.count() > 1


class LoginAsBusinessSerializer(serializers.ModelSerializer):
    phone = CreatePhoneSerializer()

    class Meta:
        model = User
        fields = ("phone", "name", "language")

    def save(self):
        phone = self.validated_data.get("phone")
        user = User.objects.filter(phone=phone).first()

        if user is not None:
            return user

        return User.objects.create_user(**self.validated_data)


class UserProfileForBusinessSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()
    has_user_profile = serializers.SerializerMethodField()
    has_multiple_businesses = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "uuid",
            "name",
            "picture",
            "auth_token",
            "language",
            "has_user_profile",
            "has_multiple_businesses",
        )

    def get_auth_token(self, user):
        token = Token.objects.filter(user=user).first()
        return token.key

    def get_has_user_profile(self, user):
        profile = UserProfile.objects.filter(user=user)

        return profile.exists()

    def get_has_multiple_businesses(self, user):
        businesses = Business.objects.filter(owner__user=user)
        return businesses.count() > 1

    def get_picture(self, user):
        if hasattr(user, "profile"):
            return user.profile.picture.url
        return None
