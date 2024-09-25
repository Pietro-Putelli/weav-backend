from django.urls.conf import path

from devices.views import DeviceAPIView, logout

urlpatterns = [path("", DeviceAPIView.as_view(), name="device"),
               path("logout/", logout, name="logout")]
