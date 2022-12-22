import json
from django.db.models.signals import post_save
from django.dispatch import receiver

from pp_placehoder.generator import generate_profile_placeholder
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import UserProfile, UserFriendRequest


@receiver(post_save, sender=UserProfile)
def create_picture_placeholder(sender, instance, created, **kwargs):
    if created:
        picture = generate_profile_placeholder(instance.name)
        instance.set_picture(picture)


''''
    Send websocket message when new friend request is created
'''


@receiver(post_save, sender=UserFriendRequest)
def send_friend_requests_count(sender, instance, created, **kwargs):
    if created:
        friend = instance.friend
        socket_channel = f"user.{friend.id}"

        send_data_to_socket_channel(socket_channel, SocketActions.USER_FRIEND_REQUEST, None)
