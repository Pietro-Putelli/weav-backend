from django.db.models.signals import post_save
from django.dispatch import receiver

from posts.models import BusinessPostSlice, UserPost
from services.images import crop_image_white_line


@receiver(post_save, sender=UserPost)
def on_user_post_slice_created(instance, created, **_):
    if created:
        instance.source = crop_image_white_line(instance.source)
        instance.save()


@receiver(post_save, sender=BusinessPostSlice)
def on_business_post_slice_created(instance, created, **_):
    if created:
        instance.source = crop_image_white_line(instance.source)
        instance.save()
