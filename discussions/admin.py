from django.contrib import admin
from discussions.models import EventDiscussion, EventDiscussionMessage


@admin.register(EventDiscussion)
class EventDiscussionAdmin(admin.ModelAdmin):
    list_display = ("get_title", "get_owner", "get_members", "id")

    @admin.display(description='Event title')
    def get_title(self, discussion):
        return discussion.event.title

    @admin.display(description='Owner')
    def get_owner(self, discussion):
        return discussion.event.business

    @admin.display(description='Members')
    def get_members(self, discussion):
        return discussion.members.count()


@admin.register(EventDiscussionMessage)
class EventDiscussionMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "content")
