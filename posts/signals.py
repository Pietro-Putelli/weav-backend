from django.db.models.signals import post_save
from django.dispatch import receiver

from posts.models import BusinessPostSlice, UserPostSlice
from servicies.images import crop_image_white_line


@receiver(post_save, sender=UserPostSlice)
def post_save_user_post_slice(instance, created, **_):
    if created:
        instance.source = crop_image_white_line(instance.source)
        instance.save()


@receiver(post_save, sender=BusinessPostSlice)
def post_save_business_post_slice(instance, created, **_):
    if created:
        instance.source = crop_image_white_line(instance.source)
        instance.save()
