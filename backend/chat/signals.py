from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.serializers import BusinessChatSerializer, ChatSerializer
from devices.models import Device
from devices.utils import NotificationType
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import BusinessChatMessage, ChatMessage


@receiver(post_save, sender=ChatMessage)
def on_user_chat_created(instance, created, **_):
    message = instance

    if created:
        chat = message.chat
        msg_sender = message.sender
        msg_receiver = message.receiver

        channel_name = f"user.{msg_receiver.user.uuid}"

        chat_sender, chat_receiver = chat.sender, chat.receiver

        is_chat_sender = chat_sender == msg_sender
        is_chat_receiver = chat_receiver == msg_sender

        is_reaction = message.reaction is not None

        serialized = ChatSerializer(chat, context={"user": msg_receiver})

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, serialized.data)

        if (
            (is_chat_sender and not chat.receiver_mute)
            or (is_chat_receiver and not chat.sender_mute)
            and not is_reaction
        ):
            device = Device.objects.filter(user=msg_receiver.user).first()

            if device and not device.is_business:
                device.send_notification(NotificationType.MESSAGE, msg_sender, message)


@receiver(post_save, sender=BusinessChatMessage)
def on_business_chat_created(instance, created, **_):
    message = instance

    if created:
        is_receiver_user = message.user is not None

        chat = message.chat
        chat_user = chat.user
        chat_business = chat.business

        # User muted the chat
        sender_muted = chat.sender_mute
        receiver_muted = chat.receiver_mute

        if is_receiver_user:
            channel_name = f"user.{chat_user.user.uuid}"
            device = Device.objects.filter(user=chat_user.user).first()

            msg_sender = chat_business

        else:
            channel_name = f"business.{chat_business.uuid}"
            device = Device.objects.filter(user=chat_business.owner.user).first()

            msg_sender = chat_user

        serialized = BusinessChatSerializer(chat, context={"is_user": is_receiver_user})

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, serialized.data)

        if device is not None and (
            (is_receiver_user and not sender_muted)
            or (not is_receiver_user and not receiver_muted)
        ):
            device.send_notification(
                NotificationType.BUSINESS_MESSAGE, msg_sender, message
            )


@receiver(post_save, sender=ChatMessage)
def on_user_message_created(instance, created, **_):
    pass
