from django.db.models.query_utils import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.viewsets import ViewSet

from pp_placehoder.generator import generate_profile_placeholder
from profiles.models import UserProfile
from servicies.caches import cache_instance, get_object_from_cache
from servicies.choices import LoginChoices
from throttling.throttlers import UnAuthenticatedThrottle
from users.email import RegistrationEmail, LoginEmail
from users.functions import verify_google_ouath_token
from users.models import User, AccessToken
from users.serializers import (
    LoginSerializer,
    RegistrationSerializer, RegistrationWithSerializer,
)


class RegisterViewSet(ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (UnAuthenticatedThrottle,)

    def register(self, request):
        data = request.data

        serializer = RegistrationSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()
            email = user.email

            cache_instance(user, RegistrationSerializer, {})

            token = AccessToken.objects.create_or_update(email=email)

            RegistrationEmail(context={"token": token.value}).send(to=[email])

            return Response(status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def complete_registration(self, request):
        data = request.data

        token = data.get("token")
        email = data.get("email")

        try:
            registration_token = AccessToken.objects.get(value=token, email=email)

            user_data = get_object_from_cache(email, delete=True)

            user = User.objects.create_user(**user_data)
            user = LoginSerializer(user.profile)

            registration_token.delete()

            return Response(user.data, status=HTTP_200_OK)

        except AccessToken.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def register_with(self, request):
        data = request.data

        token = data.get("token")
        method = data.get("method")
        username = data.get("username")

        user_data = None

        if method == LoginChoices.GOOGLE:
            user_data = verify_google_ouath_token(token)

        if user_data is not None:
            serializer = RegistrationWithSerializer(data=user_data)

            if serializer.is_valid():
                user = serializer.save(username)
                response = LoginSerializer(user.profile).data

                return Response(response, status=HTTP_200_OK)

        return Response(status=HTTP_400_BAD_REQUEST)

    def resend_registration_token(self, request):
        email = request.data.get("email")

        user = get_object_from_cache(email)

        if user:
            token = AccessToken.objects.create_or_update(email=email)

            RegistrationEmail(context={"token": token.value}).send(to=[email])

            return Response(status=HTTP_200_OK)

        return Response(status=HTTP_404_NOT_FOUND)


class LoginViewSet(ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (UnAuthenticatedThrottle,)

    def login(self, request):
        data = request.data

        email = data.get("email")
        username = data.get("username")

        try:
            user = User.objects.get(Q(email=email) | Q(username=username))
        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        token = AccessToken.objects.create_or_update(email=user.email)

        LoginEmail(context={"token": token.value}).send(to=[user.email])

        return Response(status=HTTP_200_OK)

    def complete_login(self, request):
        data = request.data

        token = data.get("token")
        email = data.get("email")

        try:
            registration_token = AccessToken.objects.get(value=token, email=email)

            user = User.objects.get(email=email)
            serialized = LoginSerializer(user.profile)

            registration_token.delete()

            return Response(serialized.data, status=HTTP_200_OK)

        except AccessToken.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def login_with(self, request):
        data = request.data
        token = data.get("token")

        response = None
        user_data = verify_google_ouath_token(token)

        if user_data is not None:
            email = user_data.get("email")
            user = User.objects.get_or_none(email)

            if user:
                response = LoginSerializer(user.profile).data
        else:
            return Response(status=HTTP_400_BAD_REQUEST)
        return Response(response, status=HTTP_200_OK)

    def resend_login_token(self, request):
        data = request.data
        email = data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        token = AccessToken.objects.create_or_update(email=user.email)
        LoginEmail(context={"token": token.value}).send(to=[user.email])

        return Response(status=HTTP_200_OK)


@api_view(["POST"])
def set_user_public_key(request):
    public_key = request.data.get("public_key")
    request.user.profile.set_public_key(public_key)
    return Response(status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def check_user_existence(request):
    data = request.query_params

    email = data.get("email")
    username = data.get("username")

    try:
        if email is not None:
            User.objects.get(email=email)
        else:
            User.objects.get(username=username)

        return Response(status=HTTP_200_OK)
    except User.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


'''
    TESTS
'''


@api_view(["GET"])
@permission_classes([AllowAny])
def send_test_email(request):
    # TokenVerificationEmail(context={"code": "56754682"}).send(to=["pietroputelli80@gmail.com"])
    picture = generate_profile_placeholder("Pietro Putelli")
    profile = UserProfile.objects.get(id=25)

    profile.set_picture(picture)
    return Response(status=HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def create_user(request):
    data = request.data

    name = data.get("name")
    email = data.get("email")
    username = data.get("username")

    user = User.objects.create_user(username=username, email=email, name=name)

    return Response(status=HTTP_200_OK)
