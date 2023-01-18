from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ValidationError

from profiles.models import UserProfile
from users.email import WelcomeEmail
from users.models import User
from users.utils import UserCache


class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        model = User
        fields = ("username", "email", "name")

    def validate_username(self, username):
        try:
            User.objects.get(username=username)
            raise ValidationError("Username already exists")
        except ObjectDoesNotExist:
            return username

    def validate_email(self, email):
        try:
            User.objects.get(email=email)
            raise ValidationError("Email already exists")
        except ObjectDoesNotExist:
            return email

    def save(self):
        return UserCache(**self.validated_data)


class RegistrationWithSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField()

    def save(self, username):
        email = self.validated_data.get("email")
        name = self.validated_data.get("name")

        user = User.objects.create_user(email=email, username=username, name=name)

        WelcomeEmail(context={"username": username}).send(to=[email])

        return user


class AuthenticationSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            raise ValidationError("Authentication failed")

        return user


class LoginSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    auth_token = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

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
        )

    def get_id(self, profile):
        return profile.user.uuid

    def get_auth_token(self, profile):
        return Token.objects.get(user=profile.user).key

    def get_username(self, profile):
        return profile.user.username
