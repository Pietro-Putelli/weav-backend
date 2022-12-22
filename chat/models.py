from django.utils import timezone
from django.db import models
from django.db.models import CASCADE

from chat.managers import (BusinessChatManager, BusinessChatMessageManager,
                           ChatManager, ChatMessageManager)
from core.models import TimestampModel

"""
    The CONTENT field can be empty because a user can share a story (identified by field 'user_story' or 'venue_story').
    The REPLY field refers to another message and can be empty.
"""

foreignkey_params = {"on_delete": CASCADE, "blank": True, "null": True}


class ChatMessageReactions(models.TextChoices):
    HEY = 'HEY', 'hey'
    EMOJI = 'EMOJI', 'emoji'


class Message(TimestampModel):
    content = models.TextField(blank=True, null=True)
    reply = models.ForeignKey("self", default=None, **foreignkey_params)
    seen = models.BooleanField(default=False)

    # Use this field to share user and venue profile
    user_profile = models.ForeignKey("users.User", db_index=False, **foreignkey_params)
    business_profile = models.ForeignKey("business.Business", db_index=False, **foreignkey_params)

    user_moment = models.ForeignKey("moments.UserMoment", db_index=False, **foreignkey_params)
    event_moment = models.ForeignKey("moments.EventMomentSlice", db_index=False,
                                     **foreignkey_params)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} • {self.content}"


class ChatMessage(Message):
    chat = models.ForeignKey("Chat", on_delete=CASCADE)

    sender = models.ForeignKey(
        "users.User", on_delete=CASCADE, db_index=False, related_name="sender")

    receiver = models.ForeignKey(
        "users.User", on_delete=CASCADE, db_index=False, related_name="receiver")

    reaction = models.CharField(
        max_length=32, choices=ChatMessageReactions.choices, null=True, blank=True
    )

    objects = ChatMessageManager()


class AbstractChat(TimestampModel):
    muted_by = models.ManyToManyField("users.User", blank=True,
                                      related_name="%(app_label)s_%(""class)s_chat_muted")

    class Meta:
        abstract = True

    def update_date(self):
        self.updated_at = timezone.now()
        self.save()


class Chat(AbstractChat):
    sender = models.ForeignKey(
        "users.User", on_delete=CASCADE, db_index=False, related_name="chat_sender")
    receiver = models.ForeignKey(
        "users.User", on_delete=CASCADE, db_index=False, related_name="chat_receiver")

    # The last message appears when use deleted the chat
    sender_deleted_to = models.ForeignKey(
        ChatMessage, **foreignkey_params, related_name="sender_deleted_to"
    )
    receiver_deleted_to = models.ForeignKey(
        ChatMessage, **foreignkey_params, related_name="receiver_deleted_to"
    )

    # To know if the receiver want to start chat
    is_active = models.BooleanField(default=False)

    def activate(self):
        self.is_active = True
        self.save()

    objects = ChatManager()

    class Meta:
        indexes = [models.Index(fields=["sender", "receiver"])]

    def __str__(self):
        return f"{self.id} • {self.sender.username} • {self.receiver.username}"


class BusinessChat(AbstractChat):
    user = models.ForeignKey("users.User", db_index=False, on_delete=CASCADE)
    business = models.ForeignKey("business.Business", db_index=False, **foreignkey_params)

    objects = BusinessChatManager()

    class Meta:
        indexes = [models.Index(fields=["user", "business"])]

    def __str__(self):
        return f"{self.user.username} • {self.business.name}"


class BusinessChatMessage(TimestampModel):
    chat = models.ForeignKey("BusinessChat", on_delete=CASCADE)

    # In case user is None, the message is from user side.
    user = models.ForeignKey("users.User", **foreignkey_params)

    content = models.TextField(max_length=256, blank=True, null=True)
    reply = models.ForeignKey("self", default=None, **foreignkey_params)
    seen = models.BooleanField(default=False)

    objects = BusinessChatMessageManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.chat.id} • {self.content}"
