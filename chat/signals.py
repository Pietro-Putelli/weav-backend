from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.serializers import BusinessChatSerializer, ChatSerializer
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from .models import BusinessChatMessage, ChatMessage


@receiver(post_save, sender=ChatMessage)
def send_user_chat(instance, created, **_):
    if created:
        channel_name = f"user.{instance.receiver.id}"

        chat = ChatSerializer(instance.chat, context={
            "user": instance.receiver}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)


@receiver(post_save, sender=BusinessChatMessage)
def send_business_chat(instance, created, **_):
    if created:
        is_receiver_user = instance.user is not None

        chat = instance.chat

        if is_receiver_user:
            channel_name = f"user.{chat.user.id}"
        else:
            business = chat.business
            channel_name = f"business.{business.id}"

        chat = BusinessChatSerializer(
            chat, context={"is_user": is_receiver_user}).data

        send_data_to_socket_channel(channel_name, SocketActions.CHAT, chat)
