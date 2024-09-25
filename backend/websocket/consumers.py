import json
from .utils import align_user_data

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.chat_types import ChatTypes
from chat.models import BusinessChat, BusinessChatMessage
from chat.serializers import BusinessChatMessageSerializer
from chat.utils import create_business_message, create_user_message, create_discussion_message
from websocket.actions import SocketActions


class ChatConsumer(AsyncWebsocketConsumer):
    # Receive data from send_message in frontend
    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.actions[data["action"]](data)

    # Send message to group ws url
    async def send_to_group(self, action, content):
        await self.channel_layer.group_send(
            self.chat_group_name,
            {"type": "send_data", "action": action, "content": content},
        )

    async def send_data(self, event):
        response = json.dumps({"action": event["action"], "content": event["content"]})
        await self.send(response)


class UserChatConsumer(ChatConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        self.user = None
        self.profile = None
        self.chat_group_name = None
        self.actions = {
            SocketActions.MESSAGE: self.send_message,
        }

    async def connect(self):
        self.user = self.scope.get("user")

        if self.user is not None:
            self.chat_group_name = f"user.{self.user.uuid}"

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
            await self.accept()

            await align_user_data(self.user)
        else:
            await self.close()

    async def disconnect(self, code):
        if self.user is not None:
            await self.channel_layer.group_discard(
                self.chat_group_name, self.channel_name
            )

    # DATABASE: create message for ChatMessageScreen
    @database_sync_to_async
    def create_db_message(self, data):
        message = data.get("message")
        temporary_id = message.get("id")
        chat_type = message.get("chat_type")

        profile = self.user.profile

        try:
            if chat_type == ChatTypes.USER_TO_USER:
                message = create_user_message(message, profile)
            elif chat_type == ChatTypes.BUSINESS:
                message = create_business_message(message)
            else:
                message = create_discussion_message(message, profile)

        except ValueError:
            return None, None

        return temporary_id, message

    # ACTION-1: send_message used in ChatMessageScreen
    async def send_message(self, data):
        temporary_id, message = await self.create_db_message(data)

        if temporary_id is None:
            await self.send_to_group(SocketActions.CHAT_DOES_NOT_EXIST, "")
        else:
            message = json.dumps(message)
            response = json.dumps({"temp_id": temporary_id, "message": message})

            await self.send_to_group(SocketActions.MESSAGE, response)


class BusinessChatConsumer(ChatConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        self.business = None
        self.chat_group_name = None
        self.actions = {
            SocketActions.MESSAGE: self.send_message,
        }

    async def connect(self):
        self.business = self.scope.get("business")

        if self.business is not None:
            self.chat_group_name = f"business.{self.business.uuid}"

            await self.channel_layer.group_add(self.chat_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, code):
        if self.business is not None:
            await self.channel_layer.group_discard(
                self.chat_group_name, self.channel_name
            )

    @database_sync_to_async
    def create_db_message(self, data):
        message = data.get("message")

        chat_id = message.get("chat_id")
        temporary_id = message.get("id")
        content = message.get("content")

        chat = BusinessChat.objects.get(id=chat_id)

        message = BusinessChatMessage.objects.create(
            chat=chat,
            user=chat.user,
            content=content,
        )

        message = BusinessChatMessageSerializer(message).data

        return temporary_id, message

    # ACTION-1: send_message used in ChatMessageScreen

    async def send_message(self, data):
        temporary_id, message = await self.create_db_message(data)

        message = json.dumps(message)
        response = json.dumps({"temp_id": temporary_id, "message": message})

        await self.send_to_group(SocketActions.MESSAGE, response)
