from celery import shared_task
from moments.models import EventMoment, UserMoment


@shared_task
def delete_expired_moment(moment_id):
    UserMoment.objects.filter(id=moment_id).delete()


@shared_task
def delete_expired_event(event_id):
    EventMoment.objects.filter(id=event_id).delete()
