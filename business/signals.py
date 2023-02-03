import os

from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from business.models import Business, BusinessToken
from devices.models import Device
from devices.utils import NotificationType


@receiver(post_save, sender=Business)
def post_save_business(instance, created, **_):
    if created:
        # 1. Generate token

        BusinessToken.objects.create(business=instance)

        # 2. Change folder name according to business id

        owner_id = instance.owner.id

        dir_path = os.path.join(
            settings.MEDIA_ROOT, f"{owner_id}/business"
        )

        dir_new_path = f"{dir_path}/{instance.id}/"
        none_path = f"{dir_path}/None"

        if os.path.exists(none_path):
            os.rename(none_path, dir_new_path)

        source_path = f"{owner_id}/business/{instance.id}/"

        cover = instance.cover_source
        cover_name = os.path.basename(cover.url)
        new_cover_path = os.path.join(source_path, cover_name)

        instance.update_cover(new_cover_path)


@receiver(pre_save, sender=Business)
def on_change_business(instance, **_):
    if instance.id is not None:
        previous = Business.objects.get(id=instance.id)
        if previous.is_approved != instance.is_approved:

            if instance.is_approved:
                device = Device.objects.filter(user=instance.owner).first()

                if device:
                    device.send_notification(None, instance, NotificationType.BUSINESS_APPROVED)
