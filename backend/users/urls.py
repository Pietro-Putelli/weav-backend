from django.urls import path

from users.views import (
    UserAPIView,
    check_user_existence,
    LoginOTPViewSet,
    login_as_business,
    accept_terms,
    SignUpViewSet,
    login_with_token,
    SocialLoginViewSet,
)

urlpatterns = [
    path("", UserAPIView.as_view(), name="user"),
    path("exists/", check_user_existence, name="check_user_existence"),
    path(
        "login-otp/",
        LoginOTPViewSet.as_view({"get": "request_otp"}),
        name="request_otp",
    ),
    path(
        "login-otp/verify/",
        LoginOTPViewSet.as_view({"post": "verify_opt"}),
        name="verify_opt",
    ),
    path(
        "phone-signup/",
        SignUpViewSet.as_view({"post": "phone_signup"}),
        name="phone_signup",
    ),
    path(
        "username-signup/",
        SignUpViewSet.as_view({"post": "username_signup"}),
        name="username_signup",
    ),
    path("token-login/", login_with_token, name="login_with_token"),
    path("login-as-business/", login_as_business, name="login_as_business"),
    path("accept-terms/", accept_terms, name="accept_terms"),
    path(
        "social/verify/",
        SocialLoginViewSet.as_view({"post": "verify"}),
        name="social_verify",
    ),
    path(
        "social/login/",
        SocialLoginViewSet.as_view({"post": "login"}),
        name="social_login",
    ),
]
