import os

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from business.models import Business, BusinessToken


@receiver(post_save, sender=Business)
def rename_business_dir(instance, created, **__):
    if created:
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


@receiver(post_save, sender=Business)
def create_auth_token(instance, created, **kwargs):
    if created:
        BusinessToken.objects.create(business=instance)
