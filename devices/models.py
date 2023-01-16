from django.db import models

from devices.managers import DeviceManager
from devices.utils import send_ios_notification, send_android_notification, get_notifications_body


class Device(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    token = models.CharField(max_length=255)

    objects = DeviceManager()

    def send_notification(self, sender, message):
        username, msg_body = get_notifications_body(sender, message)

        args = (self.token, username, msg_body)

        if len(self.token) <= 64:
            send_ios_notification(*args)
        else:
            send_android_notification(*args)
