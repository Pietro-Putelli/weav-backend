import os
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from users.models import User
import shutil


@receiver(post_save, sender=User)
def on_user_created(instance, created, **_):
    user = instance

    if not created:
        return

    Token.objects.create(user=user)


@receiver(post_delete, sender=User)
def on_user_deleted(instance, **_):
    user = instance

    user_dir = os.path.join(settings.MEDIA_ROOT, "users", user.uuid)

    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
