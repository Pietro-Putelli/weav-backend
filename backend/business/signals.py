import os
import shutil

from django.conf import settings
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from business.models import Business, BusinessToken
from devices.models import Device
from devices.utils import NotificationType


@receiver(post_save, sender=Business)
def on_business_created(instance, created, **_):
    if created:
        # Create Token
        BusinessToken.objects.create(business=instance)

        # Change device logged as business
        Device.objects.filter(user=instance.owner.user).update(is_logged=True)


@receiver(pre_save, sender=Business)
def on_business_changed(instance, **_):
    if instance.id is not None:
        previous = Business.objects.get(id=instance.id)
        if previous.is_approved != instance.is_approved:
            if instance.is_approved:
                device = Device.objects.filter(user=instance.owner.user).first()

                if device:
                    device.send_notification(
                        NotificationType.BUSINESS_APPROVED, message=instance
                    )


@receiver(post_delete, sender=Business)
def on_business_deleted(instance, **_):
    business = instance
    user = business.owner.user

    user_dir = os.path.join(
        settings.MEDIA_ROOT, "users", user.uuid, "business", business.uuid
    )

    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)

    if business.location is not None:
        business.location.delete()

    if business.timetable is not None:
        business.timetable.delete()
