from django.db.models.query_utils import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND
from rest_framework.viewsets import ViewSet

from authentication.api_views import (
    AuthenticationMixinAPIView,
    AuthenticationMixinViewSet,
)
from authentication.decorators import authentication_mixin
from authentication.decorators import business_authentication
from business.models import Business
from chat.functions import get_my_chats, get_business_chats, get_chat_model
from chat.models import (
    BusinessChat,
    BusinessChatMessage,
    Chat,
    ChatMessage,
    ChatMessageReactions,
)
from chat.serializers import (
    BusinessChatMessageSerializer,
    BusinessChatSerializer,
    ChatMessageSerializer,
    ChatSerializer,
)
from insights.utils import add_share_to_event, add_share_to_business
from moments.models import EventMoment, UserMoment
from profiles.models import UserProfile
from services.date import today_date
from services.utils import cast_to_int
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

            my_profile = request.user.profile
            receiver_profile = receiver.profile

            chat = Chat.objects.create(sender=my_profile, receiver=receiver_profile)

            ChatMessage.objects.create(
                sender=my_profile, receiver=receiver_profile, chat=chat, content=content
            )

            chat = ChatSerializer(chat, context={"user": my_profile}).data

        return Response(chat, status=HTTP_200_OK)

    def get(self, request):
        params = request.query_params

        offset = cast_to_int(params.get("offset"))

        user = request.user or request.business

        chats = get_my_chats(user, offset)

        response = {"chats": chats}

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

        queryset.delete()

        return Response(status=HTTP_200_OK)


# Handle messages for both user and business
class MessagesViewSet(AuthenticationMixinViewSet):
    def _get_params(self, request):
        params = request.query_params

        chat_id = cast_to_int(params.get("chat_id"))
        offset = cast_to_int(params.get("offset"))
        up_offset = offset + MESSAGES_LIMIT

        return chat_id, offset, up_offset

    def user_messages(self, request):
        chat_id, offset, up_offset = self._get_params(request)

        profile = request.user.profile

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        messages = ChatMessage.objects.get_messages(chat.id, profile)[offset:up_offset]
        messages = ChatMessageSerializer(
            messages, context={"user": request.user}, many=True
        )

        return Response(messages.data, status=HTTP_200_OK)

    def business_messages(self, request):
        chat_id, offset, up_offset = self._get_params(request)

        messages = BusinessChatMessage.objects.get_messages(chat_id)[offset:up_offset]
        messages = BusinessChatMessageSerializer(messages, many=True)

        return Response(messages.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_chat_by_user(request):
    receiver_id = request.query_params.get("user_id")

    receiver = User.objects.get(uuid=receiver_id)

    profile = request.user.profile

    my_chat = Chat.objects.get_chat(profile, receiver.profile)

    if my_chat is not None:
        my_chat = ChatSerializer(my_chat, context={"user": profile}).data

    return Response(my_chat, status=HTTP_200_OK)


@api_view(["GET"])
def read_messages(request):
    params = request.query_params
    profile = request.user.profile

    chat_id = params.get("chat_id")

    ChatMessage.objects.get_messages(chat_id, profile).exclude(
        sender=request.user.profile
    ).update(seen=True)

    return Response(status=HTTP_200_OK)


@api_view(["GET"])
def search_chats(request):
    params = request.query_params

    value = params.get("value")

    if len(value) == 0:
        return Response([], status=HTTP_200_OK)

    profile = request.user.profile

    chats = Chat.objects.filter(
        Q(~Q(sender=profile) & Q(sender__username__icontains=value))
        | Q(~Q(receiver=profile) & Q(receiver__username__icontains=value))
    )
    chats = ChatSerializer(chats, context={"user": profile}, many=True)

    return Response(chats.data, status=HTTP_200_OK)


# Mute user or business chats
@api_view(["PUT"])
@authentication_mixin
def mute_chat(request):
    data = request.data

    chat_id = data.get("id")
    type = data.get("type")
    is_business = data.get("is_business")

    model = get_chat_model(type)

    try:
        chat = model.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    if type == "business":
        if is_business:
            chat.receiver_mute = not chat.receiver_mute
        else:
            chat.sender_mute = not chat.sender_mute
    else:
        if chat.sender == request.user.profile:
            chat.sender_mute = not chat.sender_mute
        else:
            chat.receiver_mute = not chat.receiver_mute

    chat.save()

    return Response(status=HTTP_200_OK)


"""
    Used to share content, return new chats with content added and last messages updated.
"""


class ShareViewSet(ViewSet):
    def _get_receivers(self, request):
        receivers = request.data.get("receivers")
        return UserProfile.objects.filter(user__uuid__in=receivers)

    def moment(self, request):
        data = request.data
        profile = request.user.profile

        moment_id = data.get("moment_id")
        event_id = data.get("event_id")

        receivers = self._get_receivers(request)

        chats = []

        if moment_id:
            try:
                moment = UserMoment.objects.get(uuid=moment_id)

                for receiver in receivers:
                    chat = Chat.objects.get_or_create(profile, receiver)
                    ChatMessage.objects.create(
                        chat=chat, sender=profile, receiver=receiver, moment=moment
                    )
                    chats.append(chat)

            except UserMoment.DoesNotExist:
                return Response(status=HTTP_404_NOT_FOUND)
        else:
            try:
                event = EventMoment.objects.get(uuid=event_id)

                add_share_to_event(request.user, event)

                for receiver in receivers:
                    chat = Chat.objects.get_or_create(profile, receiver)
                    ChatMessage.objects.create(
                        chat=chat, sender=profile, receiver=receiver, event=event
                    )
                    chats.append(chat)

            except EventMoment.DoesNotExist:
                return Response(status=HTTP_404_NOT_FOUND)

        chats = ChatSerializer(chats, many=True, context={"user": profile})
        return Response(chats.data, status=HTTP_200_OK)

    def profile(self, request):
        data = request.data
        user = request.user

        mode = data.get("mode")  # user OR business
        profile_id = data.get("profile_id")
        receivers = self._get_receivers(request)

        try:
            if mode == "business":
                profile = Business.objects.get(uuid=profile_id)
            else:
                profile = UserProfile.objects.get(user__uuid=profile_id)

            data = {f"{mode}_profile": profile}

            if mode == "business":
                add_share_to_business(user, profile)

            chats = []

            profile = user.profile

            for receiver in receivers:
                chat = Chat.objects.get_or_create(profile, receiver)
                ChatMessage.objects.create(
                    chat=chat, sender=profile, receiver=receiver, **data
                )
                chats.append(chat)

            chats = ChatSerializer(chats, many=True, context={"user": user})
            return Response(chats.data, status=HTTP_200_OK)

        except (UserProfile.DoesNotExist, Business.DoesNotExist):
            return Response(status=HTTP_404_NOT_FOUND)

    def reaction(self, request):
        data = request.data
        profile = request.user.profile

        type = data.get("type", None)  # ChatMessageReactions
        content = data.get("content")
        moment_id = data.get("moment_id")
        # In case you create a reaction like HEY
        receiver_id = data.get("receiver_id")

        try:
            moment = None
            is_anonymous = False

            if not receiver_id:
                moment = UserMoment.objects.get(uuid=moment_id)
                moment.replied_by.add(profile)

                is_anonymous = moment.is_anonymous

                receiver = moment.user
            else:
                receiver = UserProfile.objects.get(user__uuid=receiver_id)

            chat = Chat.objects.get_or_create(profile, receiver)

            if is_anonymous:
                chat.set_anonymous(True)

            shared = {
                "chat": chat,
                "sender": profile,
                "receiver": receiver,
                "is_anonymous": is_anonymous,
            }

            if type == ChatMessageReactions.HEY:
                count = ChatMessage.objects.filter(
                    chat=chat,
                    created_at__lte=today_date(),
                    reaction=type,
                    is_anonymous=is_anonymous,
                ).count()

                if count == 0:
                    ChatMessage.objects.create(**shared, reaction=type)

            elif type is None:
                ChatMessage.objects.create(**shared, moment=moment)
                ChatMessage.objects.create(**shared, content=content)
            else:
                ChatMessage.objects.create(
                    **shared, moment=moment, content=content, reaction=type
                )

            chat = ChatSerializer(chat, context={"user": profile})

            response = None

            if not is_anonymous:
                response = chat.data

            return Response(response, status=HTTP_200_OK)

        except UserMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


# Create chat between a user and a business using first message.
@api_view(["POST"])
def create_business_chat(request):
    data = request.data

    content = data.get("content")
    business_id = data.get("business_id")

    try:
        business = Business.objects.get(uuid=business_id)
        profile = request.user.profile

        chat = BusinessChat.objects.create(user=profile, business=business)
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
    business_id = params.get("business_id")

    profile = request.user.profile

    chat = BusinessChat.objects.filter(user=profile, business__uuid=business_id).first()

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
