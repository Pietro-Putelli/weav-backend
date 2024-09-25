from celery import shared_task
from .models import Spot


@shared_task
def delete_expired_spot(spot_id):
    Spot.objects.filter(id=spot_id).delete()
