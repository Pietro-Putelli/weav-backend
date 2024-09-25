from celery import shared_task
from devices.models import Device
from devices.utils import NotificationType


@shared_task
def send_weekly_updates():
    devices = Device.objects.filter(is_logged=True, token__isnull=False)

    for device in devices:
        if not device.is_business:
            notification_settings = device.user.profile.settings["notifications"]

            if notification_settings["weekly_updates"]:
                device.send_notification(NotificationType.WEEKLY_UPDATES)
