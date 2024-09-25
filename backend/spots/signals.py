from backend import celery_app
from django.dispatch import receiver
from .models import Spot
from datetime import datetime, timedelta
from .tasks import delete_expired_spot
from django.db.models.signals import post_save


@receiver(post_save, sender=Spot)
def on_spot_created(instance, **_):
    spot = instance

    task_id = f"delete_spot_{spot.id}"

    eta = datetime.now() + timedelta(days=2)

    delete_expired_spot.apply_async(args=[spot.id], eta=eta, task_id=task_id)
