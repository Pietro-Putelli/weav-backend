from django.dispatch import receiver
from fieldsignals import post_save_changed

from devices.models import Device


# Keep track if the device token changes because it means the user has re-installed the app,
# so it is logged as user no more as business

@receiver(post_save_changed, sender=Device, fields=["token"])
def on_device_changed(instance, **_):
    device = instance

    device.update_is_business(False)
