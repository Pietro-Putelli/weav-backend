from django.db import models
from apns2.payload import Payload
from apns2.client import APNsClient
from devices.managers import DeviceManager


class Device(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, unique=True)
    token = models.CharField(max_length=255)

    objects = DeviceManager()

    def send_notification(self, message):
        payload = Payload(alert="Hello World!", sound="default", badge=1)
        topic = 'com.app.weav'
        client = APNsClient('../real/certificates/ios_push_notifications.cer', use_sandbox=False,
                            use_alternative_port=False)
        client.send_notification(self.token, payload, topic)
