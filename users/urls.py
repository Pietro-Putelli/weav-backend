from django.urls import path

from users.views import (
    check_user_existence,
    send_test_email,
    LoginViewSet,
    RegisterViewSet,
    set_user_public_key,
    create_user,
)

urlpatterns = [
    path("register/", RegisterViewSet.as_view({"post": "register"}), name="register"),

    path("complete_registration/", RegisterViewSet.as_view({"post": "complete_registration"}),
         name="complete_registration"),

    path("resend_registration_token/",
         RegisterViewSet.as_view({"post": "resend_registration_token"}),
         name="resend_registration_token"),

    path("register_with/", RegisterViewSet.as_view({"post": "register_with"}),
         name="register_with"),

    path("login/", LoginViewSet.as_view({"post": "login"}), name="login"),

    path("complete_login/", LoginViewSet.as_view({"post": "complete_login"}),
         name="complete_login"),

    path("resend_login_token/",
         LoginViewSet.as_view({"post": "resend_login_token"}, name="resend_login_token")),

    path("login_with/", LoginViewSet.as_view({"post": "login_with"}), name="login_with"),

    path("public_key/", set_user_public_key, name="public_key"),
    path("exists/", check_user_existence, name="check_user_existence"),

    path("send/", send_test_email),
    path("create/", create_user),
]
