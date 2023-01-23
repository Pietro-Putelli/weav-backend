from django.urls.conf import path

from devices.views import logout, set_device_token

urlpatterns = [
    path("update/", set_device_token, name="update"),
    path("logout/", logout, name="logout"),
]
