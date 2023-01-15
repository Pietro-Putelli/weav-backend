import asyncio

from django.db import models

from devices.managers import DeviceManager
from devices.utils import send_ios_notification


class Device(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    token = models.CharField(max_length=255)

    objects = DeviceManager()

    def send_notification(self, sender, message):
        asyncio.run(send_ios_notification(self.token, sender, message))
