"""
    If the related event discussion does not exists, that means the first user
    has joined the event - participants > 0 - create new one, or simply add
    the user to the discussion.
"""
from discussions.models import EventDiscussion
from discussions.serializers import EventDiscussionSerializer


def create_or_update_discussion(event, user, is_going):
    discussion, _ = EventDiscussion.objects.get_or_create(event=event)
    members = discussion.members

    if is_going:
        members.add(user)
        discussion = EventDiscussionSerializer(discussion, context={"user": user})
        return discussion.data

    members.remove(user)
    return None
