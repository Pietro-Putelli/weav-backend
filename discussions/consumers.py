import json
from channels.db import database_sync_to_async
from websocket.consumers import UserChatConsumer
from websocket.actions import SocketActions
from discussions.models import EventDiscussion, EventDiscussionMessage


class EventDiscussionConsumer(UserChatConsumer):
    @database_sync_to_async
    def create_db_message(self, data):
        message = data.get("message")

        discussion_id = message.get("discussion_id")
        temporary_id = message.get("id")
        content = message.get("content")

        try:
            discussion = EventDiscussion.objects.get(id=discussion_id)
        except EventDiscussion.DoesNotExist:
            raise ValueError("Discussion not found")

        message = EventDiscussionMessage.objects.create(discussion=discussion, sender=self.user,
                                                        content=content)

        return temporary_id, message

    async def send_message(self, data):
        temporary_id, message = await self.create_db_message(data)

        message = json.dumps(message)
        response = json.dumps({"temp_id": temporary_id, "message": message})

        await self.send_to_group(SocketActions.MESSAGE, response)
