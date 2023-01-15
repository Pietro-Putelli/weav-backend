from django.urls.conf import path

from devices.views import send_notification

urlpatterns = [
    path("send/", send_notification)
]
