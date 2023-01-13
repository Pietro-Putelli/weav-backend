from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.serializers import BusinessChatSerializer, ChatSerializer
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import BusinessChatMessage, ChatMessage


@receiver(post_save, sender=ChatMessage)
def send_user_chat(instance, created, **_):
    if created:
        channel_name = f"user.{instance.receiver.uuid}"

        chat = instance.chat
        msg_sender = instance.sender
        msg_receiver = instance.receiver

        chat_sender, chat_receiver = chat.sender, chat.receiver

        has_sender_muted_chat = chat_sender == msg_sender and chat.receiver_mute
        has_receiver_muted_chat = chat_receiver == msg_sender and chat.sender_mute

        # Use this two boolean to mute push notifications

        chat = ChatSerializer(chat, context={"user": msg_receiver}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)


@receiver(post_save, sender=BusinessChatMessage)
def send_business_chat(instance, created, **_):
    if created:
        is_receiver_user = instance.user is not None

        chat = instance.chat

        if is_receiver_user:
            channel_name = f"user.{chat.user.uuid}"
        else:
            business = chat.business
            channel_name = f"business.{business.uuid}"

        chat = BusinessChatSerializer(
            chat, context={"is_user": is_receiver_user}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)
