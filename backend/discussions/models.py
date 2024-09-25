from django.utils import timezone

from chat.models import AbstractChat
from core.models import TimestampModel
from django.db import models

from discussions.managers import EventDiscussionMessageManager


class EventDiscussion(AbstractChat):
    event = models.OneToOneField(
        "moments.EventMoment", blank=True, null=True, on_delete=models.CASCADE
    )
    members = models.ManyToManyField(
        "profiles.UserProfile", blank=True, related_name="event_members"
    )
    muted_by = models.ManyToManyField(
        "profiles.UserProfile",
        related_name="muted_by_users",
        blank=True,
    )

    def __str__(self):
        return f"{self.event.id} • {self.event.business.name}"


"""
    The sender field can be null, and if so, the message is written by the owner, accessible 
    through discussion.event.business.
    
    Remember not to set a char limit for TextField because content will be saved in base 64 format.
"""


class EventDiscussionMessage(TimestampModel):
    discussion = models.ForeignKey(
        "EventDiscussion",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="discussion_message",
    )

    sender = models.ForeignKey(
        "profiles.UserProfile",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="discussion_sender",
    )

    content = models.TextField()

    objects = EventDiscussionMessageManager()

    class Meta:
        ordering = ["-created_at"]

    def update_date(self):
        self.updated_at = timezone.now()
        self.save()
