import random
import string

from django.db.models.query_utils import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_404_NOT_FOUND)
from rest_framework.viewsets import ViewSet

from business.authentication import business_authentication
from business.models import Business
from chat.functions import get_my_chats, get_business_chats, get_chat_model
from chat.models import (BusinessChat, BusinessChatMessage, Chat, ChatMessage,
                         ChatMessageReactions)
from chat.serializers import (BusinessChatMessageSerializer,
                              BusinessChatSerializer, ChatMessageSerializer,
                              ChatSerializer)
from core.authentication import authentication_mixin, AuthenticationMixinAPIView
from insights.utils import add_share_to_event, add_share_to_business
from moments.models import EventMomentSlice, UserMoment, EventMoment
from servicies.date import today_date
from servicies.utils import cast_to_int
from users.models import User

MESSAGES_LIMIT = 10
CLUB_MEMBERS_LIMIT = 8
MY_ALBUMS_LIMIT = 8


# Use to create and delete chats
class ChatView(AuthenticationMixinAPIView):
    # Create chat using first message
    def post(self, request):
        data = request.data

        content = data.get("content")
        receiver_id = data.get("receiver", None)

        chat = {}

        if receiver_id is not None:
            receiver = User.objects.get(uuid=receiver_id)

            chat = Chat.objects.create(sender=request.user, receiver=receiver)

            ChatMessage.objects.create(
                sender=request.user, receiver=receiver, chat=chat, content=content
            )

            chat = ChatSerializer(chat, context={"user": request.user}).data

        return Response(chat, status=HTTP_200_OK)

    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))

        chats = get_my_chats(request.user, offset)

        response = {"chats": chats}

        # if offset == 0:
        #     chance = get_current_chance(request.user)
        #     response["chance"] = chance

        return Response(response, status=HTTP_200_OK)

    def delete(self, request):
        params = request.query_params

        chat_id = params.get("id")
        type = params.get("type")

        model = get_chat_model(type)

        try:
            queryset = model.objects.filter(id=chat_id)
        except model.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        if type == "business":
            queryset.delete()
            return Response(status=HTTP_200_OK)

        chat = queryset.first()
        last_message = ChatMessage.objects.filter(chat=chat).first()

        if request.user.id == chat.sender.id:
            chat.sender_deleted_to = last_message
        else:
            chat.receiver_deleted_to = last_message

        sender_deleted_to = chat.sender_deleted_to
        receiver_deleted_to = chat.receiver_deleted_to

        if (sender_deleted_to is not None and receiver_deleted_to is not None) and (
                chat.sender_deleted_to.id == chat.receiver_deleted_to.id
        ):
            chat.delete()
        else:
            chat.save()

        return Response(status=HTTP_200_OK)


# Handle messages for both user and business
class MessagesViewSet(ViewSet):
    def _get_params(self, request):
        params = request.query_params

        chat_id = cast_to_int(params.get("chat_id"))
        offset = cast_to_int(params.get("offset"))
        up_offset = offset + MESSAGES_LIMIT

        return chat_id, offset, up_offset

    def user_messages(self, request):
        chat_id, offset, up_offset = self._get_params(request)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        messages = ChatMessage.objects.get_all(chat, request.user)[offset:up_offset]
        messages = ChatMessageSerializer(messages, many=True)

        return Response(messages.data, status=HTTP_200_OK)

    def business_messages(self, request):
        chat_id, offset, up_offset = self._get_params(request)

        messages = BusinessChatMessage.objects.filter(chat__id=chat_id)[
                   offset:up_offset]
        messages = BusinessChatMessageSerializer(messages, many=True)

        return Response(messages.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_chat_by_user(request):
    receiver_id = request.query_params.get("user_id")

    receiver = User.objects.get(uuid=receiver_id)
    my_chat = Chat.objects.get_chat(request.user, receiver)

    if my_chat is not None:
        my_chat = ChatSerializer(my_chat, context={"user": request.user}).data

    return Response(my_chat, status=HTTP_200_OK)


@api_view(["GET"])
def read_messages(request):
    params = request.query_params

    chat_id = params.get("chat_id")

    ChatMessage.objects.filter(chat__id=chat_id).exclude(
        sender=request.user
    ).update(seen=True)

    return Response(status=HTTP_200_OK)


@api_view(["GET"])
def search_chats(request):
    params = request.query_params

    value = params.get("value")

    if len(value) == 0:
        return Response([], status=HTTP_200_OK)

    chats = Chat.objects.filter(
        Q(~Q(sender=request.user) & Q(sender__username__icontains=value))
        | Q(~Q(receiver=request.user) & Q(receiver__username__icontains=value))
    )
    chats = ChatSerializer(chats, context={"user": request.user}, many=True)

    return Response(chats.data, status=HTTP_200_OK)


# Mute user or business chats
@api_view(["PUT"])
@authentication_mixin
def mute_chat(request):
    data = request.data

    chat_id = data.get("id")
    type = data.get("type")

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    if chat.sender == request.user:
        chat.sender_mute = not chat.sender_mute
    else:
        chat.receiver_mute = not chat.receiver_mute

    chat.save()

    return Response(status=HTTP_200_OK)


'''
    Used to share content, return new chats with content added and last messages updated.
'''


class ShareViewSet(ViewSet):
    def _get_receivers(self, request):
        receivers = request.data.get("receivers")
        return User.objects.filter(uuid__in=receivers)

    def moment(self, request):
        data = request.data
        user = request.user

        moment_id = data.get("moment_id")
        event_slice_id = data.get("event_slice_id")

        receivers = self._get_receivers(request)

        chats = []

        if moment_id:
            try:
                moment = UserMoment.objects.get(uuid=moment_id)

                for receiver in receivers:
                    chat = Chat.objects.get_or_create(user, receiver.user)
                    ChatMessage.objects.create(chat=chat, sender=user, receiver=receiver.user,
                                               user_moment=moment)
                    chats.append(chat)

            except UserMoment.DoesNotExist:
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            try:
                slice = EventMomentSlice.objects.get(id=event_slice_id)

                add_share_to_event(request.user, slice.moment)

                for receiver in receivers:
                    chat = Chat.objects.get_or_create(user, receiver)
                    ChatMessage.objects.create(chat=chat, sender=user, receiver=receiver,
                                               event_moment=slice)
                    chats.append(chat)

            except EventMomentSlice.DoesNotExist:
                return Response(status=HTTP_404_NOT_FOUND)

        chats = ChatSerializer(chats, many=True, context={"user": user})
        return Response(chats.data, status=HTTP_200_OK)

    def profile(self, request):
        data = request.data
        user = request.user

        mode = data.get("mode")  # user OR business
        profile_id = data.get("profile_id")
        receivers = self._get_receivers(request)

        profile_model = User

        if mode == "business":
            profile_model = Business

        try:
            profile = profile_model.objects.get(id=profile_id)
            data = {f"{mode}_profile": profile}

            if mode == "business":
                add_share_to_business(user, profile)

            chats = []

            for receiver in receivers:
                chat = Chat.objects.get_or_create(user, receiver)
                ChatMessage.objects.create(
                    chat=chat, sender=user, receiver=receiver, **data)
                chats.append(chat)

            chats = ChatSerializer(chats, many=True, context={"user": user})
            return Response(chats.data, status=HTTP_200_OK)

        except User.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    def reaction(self, request):
        data = request.data
        user = request.user

        type = data.get("type", None)  # ChatMessageReactions
        content = data.get("content")
        moment_id = data.get("moment_id")
        # In case you create a reaction like HEY
        receiver_id = data.get("receiver_id")

        try:
            moment = None
            if not receiver_id:
                moment = UserMoment.objects.get(uuid=moment_id)
                receiver = moment.user
            else:
                receiver = User.objects.get(uuid=receiver_id)

            chat = Chat.objects.get_or_create(user, receiver)

            shared = {"chat": chat, "sender": user, "receiver": receiver}

            if type == ChatMessageReactions.HEY:
                count = ChatMessage.objects.filter(chat=chat, created_at__lte=today_date(),
                                                   reaction=type).count()
                if count == 0:
                    ChatMessage.objects.create(**shared, reaction=type)
            elif type is None:
                ChatMessage.objects.create(**shared, user_moment=moment)
                ChatMessage.objects.create(**shared, content=content)
            else:
                ChatMessage.objects.create(**shared, user_moment=moment, content=content,
                                           reaction=type)

            chat = ChatSerializer(chat, context={"user": user})
            return Response(chat.data, status=HTTP_200_OK)

        except UserMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


# Create chat between a user and a business using first message.
@api_view(["POST"])
def create_business_chat(request):
    data = request.data

    content = data.get("content")
    business_id = data.get("id")

    try:
        business = Business.objects.get(uuid=business_id)
        user = request.user

        chat = BusinessChat.objects.create(user=user, business=business)
        BusinessChatMessage.objects.create(chat=chat, content=content)

        chat = BusinessChatSerializer(chat, context={"is_user": True}).data
        return Response(chat, status=HTTP_200_OK)

    except Business.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


@api_view(["GET"])
@business_authentication
def get_my_business_chats(request):
    params = request.query_params
    offset = cast_to_int(params.get("offset"))

    chats = get_business_chats(request.business, offset)
    return Response(chats, status=HTTP_200_OK)


@api_view(["GET"])
def get_chat_for_business(request):
    params = request.query_params
    business_id = params.get("id")

    chat = BusinessChat.objects.filter(user=request.user, business__uuid=business_id).first()

    if chat is not None:
        chat = BusinessChatSerializer(chat, context={"is_user": True}).data

    return Response(chat, status=HTTP_200_OK)


@api_view(["GET"])
@authentication_mixin
def read_business_chat_messages(request):
    params = request.query_params

    chat_id = params.get("chat_id")
    is_user = params.get("is_user")

    queryset = BusinessChatMessage.objects.filter(chat__id=chat_id, seen=False)

    if is_user == "true":
        queryset = queryset.exclude(user=None)
    else:
        queryset = queryset.filter(user=None)

    queryset.update(seen=True)

    return Response(status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def test(request):
    b = request.query_params.get("b")

    RANDOM = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(
        10))

    if b == "true":
        to_user = User.objects.get(id=2)
        business = Business.objects.get(id=1)
        chat = BusinessChat.objects.get(business=business, user=to_user)

        BusinessChatMessage.objects.create(
            chat=chat,
            user=to_user,
            content="Zt+HSIePCtHCXuLFjLlKXl64YUTTHZv1RXf/gMqFtzVrjSA7rVLS4Ct7+e+/h1lj"
        )
    else:
        my_user = User.objects.get(id=2)
        user = User.objects.get(id=28)
        chat = Chat.objects.get(id=2)

        user_profile = User.objects.get(id=3)
        business_profile = Business.objects.get(id=1)

        user_moment = UserMoment.objects.get(id=3)
        event_moment = EventMomentSlice.objects.get(id=1)

        hey_reaction = ChatMessageReactions.HEY
        emoji_reaction = ChatMessageReactions.EMOJI

        ChatMessage.objects.create(
            chat=chat,
            receiver=my_user,
            sender=user,
            content="🤬",
            reaction=emoji_reaction
        )

    return Response(status=HTTP_200_OK)
