from django.db import models

from devices.managers import DeviceManager
from devices.utils import send_ios_notification, send_android_notification


class DeviceOSTypes(models.TextChoices):
    IOS = 'IOS', 'ios'
    ANDROID = 'ANDROID', 'android'


class Device(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    token = models.CharField(max_length=255, blank=True, null=True, default=None)
    os_type = models.CharField(max_length=10, choices=DeviceOSTypes.choices, default=DeviceOSTypes.IOS)

    # To know if the user is logged, and send notifications
    is_logged = models.BooleanField(default=True)
    is_business = models.BooleanField(default=False)

    @property
    def is_android(self):
        return len(self.token) > 80

    objects = DeviceManager()

    def update_is_business(self, is_business):
        self.is_business = is_business
        self.save()

    def send_notification(self, type, sender=None, message=None):
        # If the device is not logged, we don't send the notification

        if self.is_logged and self.token is not None:
            args = (self.token, type, sender, message)

            if not self.is_android:
                return send_ios_notification(*args)

            return send_android_notification(*args)

        return None
