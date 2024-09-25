from django.db.models.signals import post_save
from django.dispatch import receiver

from devices.models import Device
from devices.utils import NotificationType
from discussions.models import EventDiscussionMessage
from discussions.serializers import EventDiscussionSerializer
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel


@receiver(post_save, sender=EventDiscussionMessage)
def update_discussion_list(instance, created, **_):
    if created:
        message = instance

        sender = message.sender
        discussion = message.discussion

        members = discussion.members.all().exclude(user=sender.user)

        for member in members:
            channel_name = f"user.{member.user.uuid}"

            new_discussion = EventDiscussionSerializer(discussion)
            send_data_to_socket_channel(channel_name, SocketActions.CHAT, new_discussion.data)

            if member not in discussion.muted_by.all():
                device = Device.objects.filter(user=member.user).first()

                if device and not device.is_business:
                    device.send_notification(NotificationType.DISCUSSION_MESSAGE, sender, message)
