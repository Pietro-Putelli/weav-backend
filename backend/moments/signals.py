from datetime import datetime, timedelta

from django.db.models.signals import m2m_changed
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from fieldsignals import post_save_changed

from backend import celery_app
from devices.models import Device
from devices.utils import NotificationType
from moments.models import UserMoment, EventMoment
from moments.tasks import delete_expired_event, delete_expired_moment
from services.date import get_date_tz_aware
from services.images import crop_image_white_line, moderate_image
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel

import time


@receiver(post_delete, sender=UserMoment)
def on_moment_deleted(instance, **_):
    moment = instance

    task_id = f"delete_moment_{moment.id}"

    # Cancel previously scheduled task if it exists
    celery_app.control.revoke(task_id=task_id, terminate=True)

    if moment.location is not None:
        moment.location.delete()

    if moment.business_tag is not None:
        moment.business_tag.sub_repost()

    if moment.event is not None:
        moment.event.sub_repost()


"""
    Send websocket message when new moment is created and user is mentioned
"""


def on_moment_mentioned(instance, **_):
    moment = instance

    mentioned_users = moment.participants.all()
    sender = moment.user

    if mentioned_users.count() > 0:
        for profile in mentioned_users:
            socket_channel = f"user.{profile.user.uuid}"
            data = {"id": moment.id}

            send_data_to_socket_channel(
                socket_channel, SocketActions.USER_MENTION_MOMENT, data
            )

            device = Device.objects.filter(user=profile.user).first()

            if device and not device.is_business:
                device.send_notification(
                    NotificationType.MOMENT_MENTION, sender, moment
                )


m2m_changed.connect(on_moment_mentioned, sender=UserMoment.participants.through)


@receiver(post_save, sender=UserMoment)
def on_moment_created(instance, created, **_):
    if not created:
        return

    time.sleep(5)

    source = instance.source
    does_source_exist = bool(source)

    if does_source_exist:
        if not moderate_image(source.url):
            UserMoment.objects.filter(id=instance.id).delete()
            return

        instance.source = crop_image_white_line(source)
        instance.save()

    moment_id = instance.id
    task_id = f"delete_moment_{instance.id}"

    delete_expired_moment.apply_async(
        args=[moment_id], eta=instance.end_at, task_id=task_id
    )


"""
    Send push notification when a new event is created
"""


def get_event_task_data(event):
    date = event.date
    start_time = event.time
    end_time = event.end_time

    if end_time < start_time:
        date += timedelta(days=1)

    event_datetime_naive = datetime.combine(date, end_time)
    event_datetime_aware = get_date_tz_aware(event_datetime_naive)

    task_id = f"delete_event_{event.id}"

    return event_datetime_aware, task_id


@receiver(post_save, sender=EventMoment)
def on_event_created(instance, created, **_):
    if not created:
        return

    # 1. Send Push Notification

    event = instance
    sender = event.business

    # Users that liked the venue
    profiles = event.business.likes.all().exclude(user=sender.owner.user)

    for profile in profiles:
        notification_settings = profile.settings["notifications"]

        all_disabled = notification_settings["all"]
        allowed = notification_settings.get("new_events", True)

        if not all_disabled and allowed:
            device = Device.objects.filter(user=profile.user).first()

            if device and not device.is_business:
                device.send_notification(NotificationType.NEW_EVENT, sender, event)


@receiver(post_save_changed, sender=EventMoment, fields=["date", "end_time"])
def on_event_changed(instance, **_):
    event = instance

    # If the event is not periodic schedule deletion task
    if event.periodic_day is None:
        eta, task_id = get_event_task_data(event)
        # Cancel previously scheduled task if it exists
        celery_app.control.revoke(task_id, terminate=True)

        # Schedule deletion task for when moment ends with a custom id
        delete_expired_event.apply_async(args=[event.id], eta=eta, task_id=task_id)


@receiver(post_delete, sender=EventMoment)
def on_event_deleted(instance, **_):
    event = instance

    task_id = f"delete_event_{event.id}"

    # Cancel previously scheduled task if it exists
    celery_app.control.revoke(task_id=task_id, terminate=True)
