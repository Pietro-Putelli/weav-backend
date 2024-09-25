from django.db.models.signals import post_save
from django.dispatch import receiver
from services.telegram import send_telegram
from devices.models import Device
from devices.utils import NotificationType
from pp_placehoder.generator import generate_profile_placeholder
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import UserProfile, UserFriendRequest, UserFriend


@receiver(post_save, sender=UserProfile)
def on_user_profile_created(instance, created, **_):
    if created:
        user = instance.user

        Device.objects.filter(user=user).update(is_business=False)

        message = f"{instance.username} / {user.name} joined Weav"

        send_telegram(message)


"""'
    Send websocket message when new friend request is created
"""


@receiver(post_save, sender=UserFriendRequest)
def on_friend_request_created(instance, created, **_):
    if created:
        user = instance.user
        friend = instance.friend
        socket_channel = f"user.{friend.user.uuid}"

        data = {"id": instance.id}

        send_data_to_socket_channel(
            socket_channel, SocketActions.USER_FRIEND_REQUEST, data
        )

        device = Device.objects.filter(user=friend.user).first()

        if device and not device.is_business:
            device.send_notification(NotificationType.FRIEND_REQUEST, user, friend)


@receiver(post_save, sender=UserFriend)
def on_user_friend_created(instance, created, **_):
    if created:
        device = Device.objects.filter(user=instance.user.user).first()

        if device and not device.is_business:
            device.send_notification(
                NotificationType.FRIEND_REQUEST_ACCEPTED, instance.friend, instance.user
            )
