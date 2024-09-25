import os
from django.db import models
from django.dispatch import receiver
from django.db.models import FileField


@receiver(models.signals.post_delete, sender=FileField)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
