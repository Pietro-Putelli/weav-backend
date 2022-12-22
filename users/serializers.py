import uuid

from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.serializers import ValidationError

from profiles.models import UserProfile
from users.email import WelcomeEmail
from users.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password"]
        extra_kwargs = {"password": {"write_only": True}}

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

    def validate_phone(self, phone):
        try:
            User.objects.get(phone=phone)
            raise ValidationError("Phone already exists")
        except ObjectDoesNotExist:
            return phone

    def save(self, name):
        email = self.validated_data.get("email")
        phone = self.validated_data.get("phone")
        password = self.validated_data.get("password")
        username = self.validated_data.get("username")

        user = User(email=email, phone=phone, username=username)
        user.set_password(password)
        user.save()

        UserProfile.objects.create(user=user, name=name)

        if email is not None:
            WelcomeEmail(context={"username": username}).send(
                to=[email])

        return user


class RegistrationWithSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField()

    def save(self, username):
        email = self.validated_data.get("email")
        name = self.validated_data.get("name")

        password = str(uuid.uuid4())

        user = User(email=email, username=username)
        user.set_password(password)
        user.save()

        UserProfile.objects.create(user=user, name=name)

        if email is not None:
            WelcomeEmail(context={"username": username}).send(
                to=[email])

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
        return profile.user.id

    def get_auth_token(self, profile):
        return Token.objects.get(user=profile.user).key

    def get_username(self, profile):
        return profile.user.username
