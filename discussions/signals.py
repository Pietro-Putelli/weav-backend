from django.db.models.signals import post_save
from django.dispatch import receiver

from discussions.models import EventDiscussionMessage
from discussions.serializers import EventDiscussionSerializer
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel


@receiver(post_save, sender=EventDiscussionMessage)
def update_discussion_list(instance, created, **_):
    sender = instance.sender
    discussion = instance.discussion

    members = discussion.members.all().exclude(uuid=sender.uuid)

    if created:
        for member in members:
            channel_name = f"user.{member.uuid}"

            new_discussion = EventDiscussionSerializer(discussion)
            send_data_to_socket_channel(channel_name, SocketActions.CHAT, new_discussion.data)
