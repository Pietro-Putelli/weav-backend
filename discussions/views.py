from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK

from core.authentication import authentication_mixin
from core.querylimits import QueryLimits
from discussions.models import EventDiscussion, EventDiscussionMessage
from discussions.serializers import EventDiscussionMessageSerializer
from servicies.utils import cast_to_int


def get_discussion_or_none(request):
    discussion_id = (request.data or request.query_params).get("id")

    try:
        return EventDiscussion.objects.get(id=discussion_id)
    except EventDiscussion.DoesNotExist:
        return None


@api_view(["PUT"])
@authentication_mixin
def mute_discussion(request):
    discussion = get_discussion_or_none(request)

    if discussion is None:
        return Response(status=HTTP_404_NOT_FOUND)

    user = request.user
    muted_by = discussion.muted_by

    if user in muted_by.all():
        muted_by.remove(user)
    else:
        muted_by.add(user)

    return Response(status=HTTP_200_OK)


@api_view(["DELETE"])
@authentication_mixin
def delete_discussion(request):
    discussion = get_discussion_or_none(request)

    if discussion is None:
        return Response(status=HTTP_404_NOT_FOUND)

    user = request.user

    discussion.members.remove(user)
    discussion.event.participants.remove(user)

    return Response(status=HTTP_200_OK)


@api_view(["GET"])
@authentication_mixin
def get_messages(request):
    params = request.query_params

    discussion_id = params.get("id")
    offset = cast_to_int(params.get("offset"))
    up_offset = offset + 10

    messages = EventDiscussion.objects.filter(id=discussion_id)[offset:up_offset]
    messages = EventDiscussionMessageSerializer(messages, many=True)

    return Response(messages.data, status=HTTP_200_OK)
