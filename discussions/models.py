from django.utils import timezone

from chat.models import AbstractChat
from core.models import TimestampModel
from django.db import models

from discussions.managers import EventDiscussionMessageManager


class EventDiscussion(AbstractChat):
    event = models.OneToOneField("moments.EventMoment", on_delete=models.CASCADE)
    members = models.ManyToManyField("users.User", related_name="event_members")

    def __str__(self):
        return f"{self.event.id} • {self.event.business.name}"


'''
    The sender field can be null, and if so, the message is written by the owner, accessible 
    through discussion.event.business.
    
    Remember not to set a char limit for TextField because content will be saved in base 64 format.
'''


class EventDiscussionMessage(TimestampModel):
    discussion = models.ForeignKey("EventDiscussion", on_delete=models.CASCADE,
                                   related_name="discussion_message")

    sender = models.ForeignKey("users.User", on_delete=models.CASCADE, blank=True, null=True,
                               related_name="discussion_sender")

    content = models.TextField()

    objects = EventDiscussionMessageManager()

    class Meta:
        ordering = ["-created_at"]

    def update_date(self):
        self.updated_at = timezone.now()
        self.save()
