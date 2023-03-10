from django.db.models.signals import m2m_changed
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from devices.models import Device
from devices.utils import NotificationType
from moments.models import UserMoment, EventMoment, EventMomentSlice
from servicies.images import crop_image_white_line
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel


@receiver(post_delete, sender=UserMoment)
def post_delete_user_moment(sender, instance, **_):
    if instance.location:
        instance.location.delete()


'''
    Send websocket message when new moment is created and user is mentioned
'''


def post_save_moment_mention(instance, created, **_):
    if not created:
        return

    moment = instance

    mentioned_users = moment.users_tag.all()
    sender = moment.user

    if mentioned_users.count() > 0:
        for user in mentioned_users:
            socket_channel = f"user.{user.id}"
            data = {"id": moment.id}

            send_data_to_socket_channel(socket_channel, SocketActions.USER_MENTION_MOMENT, data)

            device = Device.objects.filter(user=user).first()

            if device:
                device.send_notification(sender, moment, NotificationType.MOMENT_MENTION)


m2m_changed.connect(post_save_moment_mention, sender=UserMoment.users_tag.through)


@receiver(post_save, sender=UserMoment)
def post_save_moment(instance, created, **_):
    if not created:
        return

    moment = instance

    instance.source = crop_image_white_line(instance.source)
    instance.save()

    sender = moment.user
    mentioned_businesses = moment.business_tag
    event_slice = moment.event

    # notification_settings = None
    #
    # if mentioned_businesses:
    #     notification_settings = mentioned_businesses.settings["notifications"]
    #
    # if event_slice:
    #     notification_settings = event_slice.moment.business.settings["notifications"]
    #
    # if not notification_settings:
    #     return
    #
    # all_disabled = notification_settings["all"]

    # if all_disabled:
    #     return
    #
    # if event_slice and notification_settings["event_repost"]:
    #     business = event_slice.moment.business
    #
    #     device = Device.objects.filter(user=business.owner).first()
    #
    #     if device:
    #         device.send_notification(sender, event_slice, NotificationType.EVENT_REPOST)
    #
    # if mentioned_businesses and notification_settings["new_tags"]:
    #     device = Device.objects.filter(user=mentioned_businesses.owner).first()
    #
    #     if device:
    #         device.send_notification(sender, moment, NotificationType.MOMENT_BUSINESS_MENTION)


'''
    Send push notification when a new event is created
'''


@receiver(post_save, sender=EventMoment)
def post_save_event(instance, created, **_):
    if not created:
        return

    event = instance

    sender = event.business

    # Users that liked the venue
    users = event.business.likes.all().exclude(id=sender.owner.id)

    for user in users:
        notification_settings = user.profile.settings["notifications"]

        all_disabled = notification_settings["all"]
        allowed = notification_settings["new_event"]

        if not all_disabled and allowed:
            device = Device.objects.filter(user=user).first()

            if device:
                device.send_notification(sender, event, NotificationType.NEW_EVENT)


@receiver(post_save, sender=EventMomentSlice)
def post_save_event_slice(instance, created, **_):
    if not created:
        return

    instance.source = crop_image_white_line(instance.source)
    instance.save()
