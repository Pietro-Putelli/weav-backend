from chat.models import BusinessChat, BusinessChatMessage, Chat, ChatMessage
from chat.serializers import BusinessChatMessageSerializer, ChatMessageSerializer
from discussions.models import EventDiscussion, EventDiscussionMessage
from discussions.serializers import EventDiscussionMessageSerializer
from profiles.models import UserProfile
from users.models import User


def create_business_message(message):
    chat_id = message.get("chat_id")
    content = message.get("content")

    try:
        chat = BusinessChat.objects.get(id=chat_id)
    except BusinessChat.DoesNotExist:
        raise ValueError("BusinessChat not found")

    message = BusinessChatMessage.objects.create(
        user=None,
        chat=chat,
        content=content
    )

    message = BusinessChatMessageSerializer(message)
    return message.data


def create_user_message(message, profile):
    chat_id = message.get("chat_id")
    receiver_id = message.get("receiver")
    content = message.get("content")

    try:
        receiver = UserProfile.objects.get(user__uuid=receiver_id)
        chat = Chat.objects.get(id=chat_id)
    except (UserProfile.DoesNotExist, Chat.DoesNotExist):
        raise ValueError("User or Chat does not exist")

    message = ChatMessage.objects.create(
        sender=profile,
        receiver=receiver,
        chat=chat,
        content=content,
    )

    message = ChatMessageSerializer(message, context={"user": profile.user})
    return message.data


def create_discussion_message(message, user):
    discussion_id = message.get("discussion_id")
    content = message.get("content")

    try:
        discussion = EventDiscussion.objects.get(id=discussion_id)
    except EventDiscussion.DoesNotExist:
        raise ValueError("Discussion does not exist")

    message = EventDiscussionMessage.objects.create(discussion=discussion, sender=user,
                                                    content=content)

    message = EventDiscussionMessageSerializer(message)
    return message.data
