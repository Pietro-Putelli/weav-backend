import json

from business.models import Business
from business.serializers import MyBusinessSerializer
from devices.models import Device
from profiles.models import BusinessProfile, UserProfile
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from services.otp import send_otp_to
from users.models import AccessToken, User
from users.serializers import (
    LoginAsBusinessSerializer,
    SocialUserSignUpSerializer,
    UserLoginSerializer,
    UserLoginWithTokenSerializer,
    UserProfileForBusinessSerializer,
)

from .serializers import UserSignUpSerializer
from .utils import verify_login_token


class LoginOTPViewSet(ViewSet):
    permission_classes = [AllowAny]

    def request_otp(self, request):
        phone = request.query_params.get("phone")

        user = User.objects.filter(phone=phone).first()

        if user is not None and not user.is_active:
            return Response(status=HTTP_403_FORBIDDEN)

        token = AccessToken.objects.create_or_update(phone=phone)

        sid = send_otp_to(phone, token.otp)

        if sid is not None:
            token.update_sid(sid)

            return Response({"sid": sid}, status=HTTP_200_OK)

        return Response(status=HTTP_404_NOT_FOUND)

    def verify_opt(self, request):
        data = request.data

        phone = data.get("phone")
        otp = data.get("otp")
        sid = data.get("sid")

        try:
            token = AccessToken.objects.get(phone=phone, otp=otp, sid=sid)
            token.delete()
        except AccessToken.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        user = User.objects.filter(phone=phone).first()

        response = None

        if user is not None:
            Device.objects.login(user)

            # If the user has a business, return it
            business_profile = BusinessProfile.objects.filter(user=user).first()

            if business_profile is not None:
                business = Business.objects.filter(owner=business_profile).first()

                accepted_terms = business_profile.accepted_terms

                business = MyBusinessSerializer(business)

                user = UserProfileForBusinessSerializer(user)

                response = {
                    "business": business.data or {},
                    "user": user.data,
                    "accepted_terms": accepted_terms,
                }

            else:
                user = UserLoginSerializer(user.profile)
                response = user.data

        return Response(response, status=HTTP_200_OK)


class SignUpViewSet(ViewSet):
    permission_classes = [AllowAny]

    def _get_body_data(self, request):
        request_body = request.data

        picture = request_body.get("picture")
        json_data = request_body.get("data")
        data = json.loads(json_data)

        return data, picture

    def phone_signup(self, request):
        data, picture = self._get_body_data(request)

        serializer = UserSignUpSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save(picture)
            Device.objects.login(user)

            user = UserLoginSerializer(user.profile)

            return Response(user.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_404_NOT_FOUND)

    # When you create the user profile from the business side
    def username_signup(self, request):
        user = request.user

        request_body = request.data

        picture = request_body.get("picture")
        data = json.loads(request_body.get("data"))

        username = data.get("username")

        Device.objects.login(user)

        # Check if the profile already exists, only for DB integrity reasons

        profile = UserProfile.objects.filter(user=user).first()

        if profile is None:
            profile = UserProfile.objects.create(
                user=user, username=username, picture=picture
            )

        profile = UserLoginSerializer(profile)

        return Response(profile.data, status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def login_with_token(request):
    user = request.user

    if user.is_active:
        Device.objects.login(user)

        response = None

        if hasattr(user, "profile") and user.profile is not None:
            user = UserLoginWithTokenSerializer(user.profile)
            response = user.data

        return Response(response, status=HTTP_200_OK)

    return Response(status=HTTP_403_FORBIDDEN)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_as_business(request):
    data = request.data

    serializer = LoginAsBusinessSerializer(data=data)

    if serializer.is_valid():
        user = serializer.save()

        business_profile, _ = BusinessProfile.objects.get_or_create(user=user)
        business_profile.accept_terms()

        business = Business.objects.filter(owner=business_profile).first()

        business = MyBusinessSerializer(business)

        Device.objects.filter(user=user).update(is_logged=False)

        user = UserProfileForBusinessSerializer(user)

        response = {
            "business": business.data,
            "user": user.data,
        }

        return Response(response, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_404_NOT_FOUND)


@api_view(["PUT"])
def accept_terms(request):
    business_profile = BusinessProfile.objects.filter(user=request.user).first()
    business_profile.accepted_terms = True
    business_profile.save()

    return Response(status=HTTP_200_OK)


class UserAPIView(APIView):
    def delete(self, request):
        request.user.delete()
        return Response(status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def check_user_existence(request):
    data = request.query_params

    username = data.get("username")

    try:
        UserProfile.objects.get(username=username)

        return Response(status=HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


class SocialLoginViewSet(ViewSet):
    permission_classes = [AllowAny]

    # Return true if the token is verified and the user object if it exists

    def verify(self, request):
        data = request.data

        token = data.get("token", None)
        method = data.get("method")

        if token is None:
            return Response(status=HTTP_400_BAD_REQUEST)

        user_email = verify_login_token(method, token)

        if user_email is not None:
            user = User.objects.filter(email=user_email).first()

            if user is not None and hasattr(user, "profile"):
                user = UserLoginSerializer(user.profile)

                return Response({"user": user.data}, status=HTTP_200_OK)

            return Response({"email": user_email}, status=HTTP_200_OK)

        return Response(status=HTTP_404_NOT_FOUND)

    def login(self, request):
        form_data = request.data

        picture = form_data.get("picture")

        if picture is None:
            return Response(status=HTTP_404_NOT_FOUND)

        data = json.loads(form_data.get("data"))

        serializer = SocialUserSignUpSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save(picture)
            Device.objects.login(user)

            user = UserLoginSerializer(user.profile)

            return Response(user.data, status=HTTP_200_OK)

        return Response(status=HTTP_404_NOT_FOUND)
