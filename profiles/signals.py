import json
from django.db.models.signals import post_save
from django.dispatch import receiver

from devices.models import Device
from devices.utils import NotificationType
from pp_placehoder.generator import generate_profile_placeholder
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import UserProfile, UserFriendRequest, UserFriend


@receiver(post_save, sender=UserProfile)
def create_picture_placeholder(instance, created, **_):
    if created:
        picture = generate_profile_placeholder(instance.name)
        instance.set_picture(picture)


''''
    Send websocket message when new friend request is created
'''


@receiver(post_save, sender=UserFriendRequest)
def send_friend_requests(instance, created, **_):
    if created:
        user = instance.user
        friend = instance.friend
        socket_channel = f"user.{friend.uuid}"

        data = {"id": instance.id}

        send_data_to_socket_channel(socket_channel, SocketActions.USER_FRIEND_REQUEST, data)

        device = Device.objects.filter(user=friend).first()

        if device:
            device.send_notification(user, _, NotificationType.FRIEND_REQUEST)


@receiver(post_save, sender=UserFriend)
def send_user_friend(instance, created, **_):
    if created:
        device = Device.objects.filter(user=instance.user).first()

        if device:
            device.send_notification(instance.friend, _,
                                     NotificationType.FRIEND_REQUEST_ACCEPTED)
