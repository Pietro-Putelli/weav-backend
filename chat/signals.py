from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.serializers import BusinessChatSerializer, ChatSerializer
from devices.models import Device
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import BusinessChatMessage, ChatMessage


@receiver(post_save, sender=ChatMessage)
def send_user_chat(instance, created, **_):
    message = instance

    if created:
        channel_name = f"user.{message.receiver.uuid}"

        chat = message.chat
        msg_sender = message.sender
        msg_receiver = message.receiver

        chat_sender, chat_receiver = chat.sender, chat.receiver

        is_chat_sender = chat_sender == msg_sender
        is_chat_receiver = chat_receiver == msg_sender

        if (is_chat_sender and not chat.receiver_mute) or (
                is_chat_receiver and not chat.sender_mute):
            device = Device.objects.filter(user=msg_receiver).first()
            device.send_notification(msg_receiver, message)

        chat = ChatSerializer(chat, context={"user": msg_receiver}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)


@receiver(post_save, sender=BusinessChatMessage)
def send_business_chat(instance, created, **_):
    message = instance

    if created:
        is_receiver_user = message.user is not None

        chat = message.chat
        chat_user = chat.user
        chat_business = chat.business

        if is_receiver_user:
            channel_name = f"user.{chat_user.uuid}"
            device = Device.objects.filter(user=chat_user).first()

            msg_sender = chat_business

        else:
            channel_name = f"business.{chat_business.uuid}"
            device = Device.objects.filter(user=chat_business.owner).first()

            msg_sender = chat_user

        device.send_notification(msg_sender, message)

        chat = BusinessChatSerializer(
            chat, context={"is_user": is_receiver_user}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)
