from profiles.models import UserProfile
from rest_framework import serializers

from business.serializers import ShortBusinessSerializer
from moments.serializers import UserMomentSerializer, EventMomentSerializer
from profiles.serializers import (
    ShortUserProfileSerializer,
    ShortUserProfileSerializer,
)
from .models import BusinessChatMessage, ChatMessage
from users.models import User

MESSAGE_SERIALIZER_FIELDS = (
    "id",
    "created_at",
    "content",
    "reply",
    "seen",
    "reaction",
)


class MessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.CharField()
    content = serializers.CharField()
    seen = serializers.BooleanField()

    moment = UserMomentSerializer()
    event = serializers.SerializerMethodField()

    user_profile = ShortUserProfileSerializer()
    business_profile = ShortBusinessSerializer()

    reaction = serializers.SerializerMethodField()

    def get_reaction(self, instance):
        return instance.reaction

    def get_user_profile(self, instance):
        if instance.user_profile is not None:
            return ShortUserProfileSerializer(instance.user_profile).data
        return None

    def get_business_profile(self, instance):
        if instance.business_profile is not None:
            return ShortBusinessSerializer(instance.business_profile).data
        return None

    def get_event(self, message):
        event = message.event

        user = self.context.get("user")

        if event is not None:
            event = EventMomentSerializer(event, context={"user": user})
            return event.data

        return None


class ChatMessageSerializer(MessageSerializer):
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    is_anonymous = serializers.BooleanField()

    class Meta:
        model = ChatMessage
        fields = ("sender", "receiver", "is_anonymous")

    def get_sender(self, chat):
        return chat.sender.user.uuid

    def get_receiver(self, chat):
        return chat.receiver.user.uuid


class ChatSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    muted = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()

    def _get_profile(self):
        user = self.context.get("user")

        if user is None:
            return None

        return user if isinstance(user, UserProfile) else user.profile

    def get_id(self, chat):
        return f"user_{chat.id}"

    def get_receiver(self, chat):
        user = self.context.get("user")

        if user == chat.sender:
            user = chat.receiver
        else:
            user = chat.sender

        return ShortUserProfileSerializer(user).data

    def get_messages(self, chat):
        profile = self._get_profile()

        messages = ChatMessage.objects.get_messages(chat.id, profile)[:10]
        messages = ChatMessageSerializer(messages, context=self.context, many=True)

        return messages.data

    def get_unread_count(self, chat):
        user = self.context.get("user")

        profile = user

        if isinstance(user, User):
            profile = user.profile

        return (
            ChatMessage.objects.get_messages(chat.id, profile)
            .filter(receiver=profile, seen=False)
            .count()
        )

    def get_muted(self, chat):
        user = self.context.get("user")

        if user == chat.sender:
            return chat.sender_mute
        return chat.receiver_mute


class BusinessChatMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    created_at = serializers.CharField()
    content = serializers.CharField()
    seen = serializers.BooleanField()
    is_user = serializers.SerializerMethodField()

    def get_is_user(self, message):
        return message.user is None


class BusinessChatSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    business = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    muted = serializers.SerializerMethodField()

    # Used to know who wants to retrieve the chats, user or business.
    def is_user(self):
        return self.context.get("is_user") is True

    def get_id(self, chat):
        return f"business_{chat.id}"

    def get_user(self, instance):
        if self.is_user():
            return None
        return ShortUserProfileSerializer(instance.user).data

    def get_business(self, instance):
        if self.is_user():
            return ShortBusinessSerializer(instance.business).data
        return None

    def get_messages(self, instance):
        messages = BusinessChatMessage.objects.filter(chat=instance)[:10]
        return BusinessChatMessageSerializer(messages, many=True).data

    def get_unread_count(self, chat):
        queryset = BusinessChatMessage.objects.filter(chat=chat)

        if self.is_user():
            return queryset.filter(seen=False).exclude(user=None).count()

        return queryset.filter(user=None, seen=False).count()

    def get_muted(self, chat):
        if self.is_user():
            return chat.sender_mute
        return chat.receiver_mute
