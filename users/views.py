from django.db.models.query_utils import Q
# from phone_verify import api
# from phone_verify.serializers import PhoneSerializer, SMSVerificationSerializer
# from phone_verify.services import send_security_code_and_generate_session_token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ViewSet

from pp_placehoder.generator import generate_profile_placeholder
from profiles.models import UserProfile
from real.throttling import UserLoginRateThrottle
from servicies.choices import LoginChoices
from servicies.otp import send_otp_to_username
from users.functions import verify_google_ouath_token
from users.models import TokenCode, User
from users.serializers import (
    LoginSerializer,
    AuthenticationSerializer,
    RegistrationSerializer, RegistrationWithSerializer,
)


class RegisterViewSet(ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (UserLoginRateThrottle,)

    def register(self, request):
        data = request.data

        serializer = RegistrationSerializer(data=data)

        if serializer.is_valid():
            name = data.get("name")
            token_value = data.get("token")
            code = data.get("code")

            try:
                token = TokenCode.objects.get(value=token_value, code=code)

                serializer.save(name)
                token.delete()

                return Response(status=HTTP_200_OK)
            except TokenCode.DoesNotExist:
                pass

        return Response(status=HTTP_400_BAD_REQUEST)

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


class LoginViewSet(ViewSet):
    permission_classes = (AllowAny,)
    throttle_classes = (UserLoginRateThrottle,)

    def login(self, request):
        serializer = AuthenticationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data

            response = LoginSerializer(user.profile)

            return Response(response.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

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
    phone = data.get("phone")
    username = data.get("username")

    try:
        if email is not None:
            User.objects.get(email=email)
        elif phone is not None:
            User.objects.get(phone=phone)
        else:
            User.objects.get(username=username)

        return Response(status=HTTP_200_OK)
    except User.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


# OTP CODE

class OTPViewSet(ViewSet):
    permission_classes = (AllowAny,)

    def request(self, request):
        params = request.query_params
        token = send_otp_to_username(params)

        if token is not None:
            return Response({"token_value": token.value}, status=HTTP_200_OK)
        return Response(status=HTTP_400_BAD_REQUEST)

    def resend(self, request):
        token_value = request.data.get("token_value")

        try:
            username = TokenCode.objects.get(value=token_value).username
            send_otp_to_username(username=username)

            return Response(status=HTTP_200_OK)
        except TokenCode.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def verify(self, request):
        data = request.data

        username = data.get("username")
        token_value = data.get("token")
        code = data.get("code")

        try:
            TokenCode.objects.get(
                username=username, value=token_value, code=code)

            return Response(status=HTTP_200_OK)
        except TokenCode.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([AllowAny])
def reset_password(request):
    data = request.data
    token_value = data.get("token")
    new_password = data.get("password")

    try:
        token = TokenCode.objects.get(value=token_value)

        user = User.objects.filter(
            Q(email=token.username) | Q(phone=token.username)
        ).first()

        user.set_password(new_password)
        user.save()

        token.delete()

        return Response(status=HTTP_200_OK)
    except TokenCode.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


class VerificationViewSet:
    pass


# class VerificationViewSet(api.VerificationViewSet):
#     permission_classes = (AllowAny,)

#     @action(
#         detail=False,
#         methods=["POST"],
#         serializer_class=PhoneSerializer,
#     )
#     def register(self, request):
#         serializer = PhoneSerializer(data=request.data)
#         if serializer.is_valid():
#             session_token = send_security_code_and_generate_session_token(
#                 str(serializer.validated_data["phone_number"])
#             )
#             return Response({"session_token": session_token}, status=HTTP_200_OK)

#         return Response(status=HTTP_400_BAD_REQUEST)

#     @action(detail=False, methods=["POST"], serializer_class=SMSVerificationSerializer)
#     def verify(self, request):
#         serializer = SMSVerificationSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         user_id = request.user.id
#         phone_number = serializer.validated_data.get("phone_number")

#         User.objects.filter(id=user_id).update(phone=phone_number)

#         return Response(status=HTTP_200_OK)


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

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    name = data.get("name")

    user = User.objects.create_user(username=username, email=email)
    user.set_password(password)

    UserProfile.objects.create(user=user, name=name)

    return Response(status=HTTP_200_OK)
