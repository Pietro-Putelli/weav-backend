from itertools import chain

from business.models import Business
from core.querylimits import QueryLimits
from discussions.models import EventDiscussion
from discussions.serializers import EventDiscussionSerializer
from profiles.models import UserProfile
from .models import BusinessChat, Chat, ChatMessage
from .serializers import BusinessChatSerializer, ChatSerializer


def last_update_key(chat):
    return chat.updated_at


def get_my_chats(user, offset=0):
    profile = user.profile

    up_offset = offset + QueryLimits.CHAT_LIST

    is_business = isinstance(user, Business)

    business_chats = BusinessChat.objects.filter(user=profile)

    user_chats = []
    discussions = []

    if not is_business:
        user_chats = Chat.objects.get_my_chats(profile)
        discussions = EventDiscussion.objects.filter(members__in=[profile])

    all_chats = chain(user_chats, business_chats, discussions)
    ordered_chats = sorted(all_chats, key=last_update_key)
    ordered_chats.reverse()

    chats = list(ordered_chats)[offset:up_offset]

    response = []

    context = {"user": profile}
    business_chat_context = {"is_user": True}

    for chat in chats:
        if isinstance(chat, Chat):
            serialized = ChatSerializer(chat, context=context)

        elif isinstance(chat, BusinessChat):
            serialized = BusinessChatSerializer(chat, context=business_chat_context)

        else:
            serialized = EventDiscussionSerializer(chat, context=context)

        response.append(serialized.data)

    return response


def get_business_chats(business, offset):
    chats = BusinessChat.objects.filter(business=business)[
            offset: offset + QueryLimits.CHAT_LIST
            ]

    ordered_chats = sorted(chats, key=last_update_key)
    ordered_chats.reverse()

    chats = BusinessChatSerializer(ordered_chats, context={"is_user": False}, many=True)
    return chats.data


def share_profile(profile_id, users, my_user):
    user_profile = UserProfile.objects.get(user__uuid=profile_id)

    chats = []

    for user in users:
        chat_params = {"sender": my_user, "receiver": user}

        chat = Chat.objects.get_or_create(**chat_params)

        ChatMessage.objects.create(**chat_params, chat=chat, user_profile=user_profile)
        chats.append(chat)

    return chats


"""
    Get corresponding chat model using type
"""


def get_chat_model(type):
    if type == "user":
        return Chat
    return BusinessChat
