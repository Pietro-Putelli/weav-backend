from django.urls import path

from users.views import (
    #     VerificationViewSet,
    reset_password,
    check_user_existence,
    OTPViewSet,
    send_test_email,
    LoginViewSet,
    RegisterViewSet,
    set_user_public_key,
    create_user,
)

urlpatterns = [
    path("register/", RegisterViewSet.as_view({"post": "register"}), name="register"),
    path(
        "register_with/",
        RegisterViewSet.as_view({"post": "register_with"}),
        name="register_with",
    ),
    path("login/", LoginViewSet.as_view({"post": "login"}), name="login"),
    path(
        "login_with/", LoginViewSet.as_view({"post": "login_with"}), name="login_with"
    ),
    path("public_key/", set_user_public_key, name="public_key"),
    # CHECK EXISTENCE
    path("exists/", check_user_existence, name="check_user_existence"),
    # OTP
    path("otp/request/", OTPViewSet.as_view({"get": "request"}), name="request_otp"),
    path("otp/resend/", OTPViewSet.as_view({"post": "resend"}), name="resend_otp"),
    path("otp/verify/", OTPViewSet.as_view({"post": "verify"}), name="verify_otp"),
    path("reset/password/", reset_password, name="reset_password"),
    # PHONE
    #     path("phone/register/", VerificationViewSet.as_view({"post": "register"}),
    #          name="phone_verification_register"),
    #     path("phone/verify/", VerificationViewSet.as_view({"post": "verify"}),
    #          name="phone_verification_verify"),
    path("send/", send_test_email),
    path("create/", create_user),
]
