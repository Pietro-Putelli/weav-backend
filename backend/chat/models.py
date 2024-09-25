from django.utils import timezone
from django.db import models
from django.db.models import CASCADE

from chat.managers import (
    BusinessChatManager,
    BusinessChatMessageManager,
    ChatManager,
    ChatMessageManager,
)
from core.models import TimestampModel

"""
    The CONTENT field can be empty because a user can share a story (identified by field 'user_story' or 'venue_story').
    The REPLY field refers to another message and can be empty.
"""

foreignkey_params = {"on_delete": CASCADE, "blank": True, "null": True}


class ChatMessageReactions(models.TextChoices):
    HEY = "HEY", "hey"
    EMOJI = "EMOJI", "emoji"


class Message(TimestampModel):
    content = models.TextField(blank=True, null=True)
    reply = models.ForeignKey("self", default=None, **foreignkey_params)
    seen = models.BooleanField(default=False)

    # Use this field to share user and venue profile
    user_profile = models.ForeignKey(
        "profiles.UserProfile", db_index=False, **foreignkey_params
    )
    business_profile = models.ForeignKey(
        "business.Business", db_index=False, **foreignkey_params
    )

    moment = models.ForeignKey(
        "moments.UserMoment", db_index=False, **foreignkey_params
    )
    event = models.ForeignKey(
        "moments.EventMoment", db_index=False, **foreignkey_params
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} • {self.content}"


class ChatMessage(Message):
    chat = models.ForeignKey("Chat", on_delete=CASCADE)

    sender = models.ForeignKey(
        "profiles.UserProfile", on_delete=CASCADE, db_index=False, related_name="sender"
    )

    receiver = models.ForeignKey(
        "profiles.UserProfile",
        on_delete=CASCADE,
        db_index=False,
        related_name="receiver",
    )

    reaction = models.CharField(
        max_length=32, choices=ChatMessageReactions.choices, null=True, blank=True
    )

    # Means that the sender does not know the receiver
    is_anonymous = models.BooleanField(default=False)

    objects = ChatMessageManager()


class AbstractChat(TimestampModel):
    sender_mute = models.BooleanField(default=False)
    receiver_mute = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def update_date(self):
        self.updated_at = timezone.now()
        self.save()


class Chat(AbstractChat):
    sender = models.ForeignKey(
        "profiles.UserProfile",
        on_delete=CASCADE,
        db_index=False,
        related_name="chat_sender",
    )
    receiver = models.ForeignKey(
        "profiles.UserProfile",
        on_delete=CASCADE,
        db_index=False,
        related_name="chat_receiver",
    )

    # To know if the receiver want to start the chat
    is_active = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)

    def activate(self):
        self.is_active = True
        self.save()

    def set_anonymous(self, is_anonymous):
        self.is_anonymous = is_anonymous
        self.save()

    objects = ChatManager()

    class Meta:
        indexes = [models.Index(fields=["sender", "receiver"])]

    def __str__(self):
        return f"{self.id} • {self.sender.username} • {self.receiver.username}"


class BusinessChat(AbstractChat):
    user = models.ForeignKey("profiles.UserProfile", db_index=False, on_delete=CASCADE)
    business = models.ForeignKey(
        "business.Business", db_index=False, **foreignkey_params
    )

    objects = BusinessChatManager()

    class Meta:
        indexes = [models.Index(fields=["user", "business"])]

    def __str__(self):
        return f"{self.user.username} • {self.business.name}"


class BusinessChatMessage(TimestampModel):
    chat = models.ForeignKey("BusinessChat", on_delete=CASCADE)

    # In case user is None, the message is from user side.
    user = models.ForeignKey("profiles.UserProfile", **foreignkey_params)

    content = models.TextField(max_length=256, blank=True, null=True)
    reply = models.ForeignKey("self", default=None, **foreignkey_params)
    seen = models.BooleanField(default=False)

    objects = BusinessChatMessageManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.chat.id} • {self.content}"
