from rest_framework import serializers

from business.serializers import ShortBusinessSerializer, ShortChatBusinessSerializer
from moments.serializers import UserMomentSerializer, EventMomentSerializer
from profiles.serializers import ShortUserProfileSerializer, ShortUserProfileChatSerializer
from .models import BusinessChatMessage, ChatMessage

MESSAGE_SERIALIZER_FIELDS = (
    "id",
    "created_at",
    "content",
    "reply",
    "seen",
    "reaction",
)


class MessageSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    created_at = serializers.CharField()
    content = serializers.CharField()
    seen = serializers.BooleanField()
    reply = serializers.SerializerMethodField()

    user_moment = UserMomentSerializer()
    event_moment = serializers.SerializerMethodField()

    user_profile = ShortUserProfileSerializer()
    business_profile = ShortBusinessSerializer()

    reaction = serializers.SerializerMethodField()

    def get_id(self, instance):
        return f"message.{instance.id}"

    def get_reply(self, instance):
        if instance.reply is not None:
            return ChatMessageSerializer(instance.reply).data
        return None

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

    def get_event_moment(self, message):
        slice = message.event_moment
        if slice is not None:
            moment = EventMomentSerializer(slice.moment, context={"selected": slice.id})
            return moment.data
        return None


class ChatMessageSerializer(MessageSerializer):
    sender = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ("sender", "receiver")

    def get_sender(self, instance):
        return instance.sender.id

    def get_receiver(self, instance):
        return instance.receiver.id


class ChatSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    receiver = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    muted = serializers.SerializerMethodField()
    is_active = serializers.BooleanField()

    def get_id(self, instance):
        return f"chat.{instance.id}"

    def get_receiver(self, chat):
        user = self.context.get("user")

        if user == chat.sender:
            user = chat.receiver
        else:
            user = chat.sender

        return ShortUserProfileChatSerializer(user).data

    def get_messages(self, instance):
        user = self.context.get("user")

        messages = ChatMessage.objects.get_all(instance, user)[:10]
        return ChatMessageSerializer(messages, many=True).data

    def get_unread_count(self, instance):
        user = self.context.get("user")
        return ChatMessage.objects.filter(
            chat=instance, receiver=user.id, seen=False
        ).count()

    def get_muted(self, instance):
        user = self.context.get("user")
        return user in instance.muted_by.all()


class BusinessChatMessageSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    created_at = serializers.CharField()
    content = serializers.CharField()
    seen = serializers.BooleanField()
    reply = serializers.SerializerMethodField()

    is_user = serializers.SerializerMethodField()

    def get_id(self, instance):
        return f"message.{instance.id}"

    def get_reply(self, instance):
        if instance.reply is not None:
            return BusinessChatMessageSerializer(instance.reply).data
        return None

    def get_is_user(self, instance):
        return instance.user is None


class BusinessChatSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    business = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    # Used to know who wants to retrieve the chats, user or business.
    def is_user(self):
        return self.context.get("is_user") is True

    def get_id(self, instance):
        return f"business.chat.{instance.id}"

    def get_user(self, instance):
        if self.is_user():
            return None
        return ShortUserProfileChatSerializer(instance.user).data

    def get_business(self, instance):
        if self.is_user():
            return ShortChatBusinessSerializer(instance.business).data
        return None

    def get_messages(self, instance):
        messages = BusinessChatMessage.objects.filter(chat=instance)[:10]
        return BusinessChatMessageSerializer(messages, many=True).data

    def get_unread_count(self, chat):
        queryset = BusinessChatMessage.objects.filter(chat=chat)

        if self.is_user():
            return queryset.filter(seen=False).exclude(user=None).count()

        return queryset.filter(user=None, seen=False).count()
