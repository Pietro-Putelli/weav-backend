from django.db import models

from devices.managers import DeviceManager
from devices.utils import send_ios_notification


class Device(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    token = models.CharField(max_length=255, blank=True, null=True, default=None)

    # To know if the user is logged, and send notifications
    is_logged = models.BooleanField(default=True)

    objects = DeviceManager()

    def send_notification(self, sender, message, type):
        # If the device is not logged, we don't send the notification

        if self.is_logged:
            args = (self.token, sender, message, type)

            if len(self.token) <= 80:
                send_ios_notification(*args)
            # else:
            #     send_android_notification(*args)
