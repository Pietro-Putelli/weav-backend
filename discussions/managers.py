from django.db.models import Manager

from chat.managers import MessageManager


class EventDiscussionMessageManager(Manager):
    def create(self, **kwargs):
        discussion = kwargs.pop("discussion")
        discussion.update_date()
        return super().create(discussion=discussion, **kwargs)
