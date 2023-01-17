from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from devices.models import Device
from devices.utils import NotificationType
from moments.models import UserMoment
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from django.db.models.signals import m2m_changed


@receiver(post_delete, sender=UserMoment)
def post_delete_user_moment(sender, instance, **kwargs):
    if instance.location:
        instance.location.delete()


'''
    Send websocket message when new moment is created and user is mentioned
'''


def post_save_send_moment_mention(instance, **_):
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
                device.send_notification(sender, _, NotificationType.MOMENT_MENTION)


m2m_changed.connect(post_save_send_moment_mention, sender=UserMoment.users_tag.through)
