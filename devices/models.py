from django.db import models

from devices.managers import DeviceManager
from devices.utils import send_ios_notification, send_android_notification


class Device(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    token = models.CharField(max_length=255)

    objects = DeviceManager()

    def send_notification(self, sender, message, type):
        args = (self.token, sender, message, type)

        if len(self.token) <= 64:
            send_ios_notification(*args)
        else:
            send_android_notification(*args)
