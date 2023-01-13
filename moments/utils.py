from itertools import groupby

from django.db.models.query_utils import Q
from datetime import datetime, timedelta
from moments.models import EventMomentSlice, EventMoment
from profiles.models import UserFriend
from servicies.utils import omit_keys
from shared.models import MiddleSource
from users.models import User


def add_users_tag(slice, usernames):
    if usernames is not None:
        users = User.objects.filter(username__in=usernames)

        for user in users:
            slice.users_tag.add(user)


def get_validated_sources(data, count):
    sources = []

    for index in range(count):
        source = data.get(f"source_{index}")

        middle_source = MiddleSource.objects.create(source=source)

        if middle_source.is_valid():
            sources.append(source)

    return sources


def create_event_moment(business, data, sources):
    from moments.serializers import CreateEventMomentSerializer

    serializer = CreateEventMomentSerializer(data=data)

    if serializer.is_valid():

        omit_keys(data, ["date", "time", "location", "title"])

        moment = EventMoment.objects.create(business=business, **data,
                                            **serializer.validated_data)

        for source in sources:
            EventMomentSlice.objects.create(moment=moment, source=source)

        return moment

    return None


def update_event_moment(business, data, sources):
    from moments.serializers import UpdateEventMomentSerializer

    moment = EventMoment.objects.get_current(business)
    deleted_slices = data.get("deleted_slices", [])

    for source in sources:
        EventMomentSlice.objects.create(moment=moment, source=source)

    if len(deleted_slices) > 0:
        EventMomentSlice.objects.filter(id__in=deleted_slices).delete()

    serializer = UpdateEventMomentSerializer(moment, data=data)

    if serializer.is_valid():
        return serializer.save()

    print(serializer.errors)

    return None


def get_event_participants(event_id, user, offset, limit):
    from .serializers import EventParticipantSerializer
    try:
        event = EventMoment.objects.get(uuid=event_id)
    except EventMoment.DoesNotExist:
        return None

    participants = event.participants.all()

    friends = UserFriend.objects.filter(Q(user=user, friend__in=participants) | Q(friend=user,
                                                                                  user__in=participants))

    count = friends.count()
    friends = friends[offset:limit + offset]

    users = []

    for friend in friends:
        if friend.user == user:
            users.append(friend.friend)
        else:
            users.append(friend.user)

    return EventParticipantSerializer({"users": users, "count": count}).data


def get_grouped_my_events(user):
    from moments.serializers import MyEventMomentSerializer

    def event_key(event):
        return MyEventMomentSerializer(event).data

    lower_bound = datetime.now() - timedelta(1)
    upper_bound = lower_bound + timedelta(8)

    events = EventMoment.objects.filter(participants__in=[user], date__gte=lower_bound,
                                        date__lte=upper_bound)

    result = {}

    for key, group in groupby(events, lambda event: event.date):
        new_key = key.strftime("%Y-%m-%d")

        if result.get(new_key) is None:
            new_group = map(event_key, list(group))
            result[new_key] = list(new_group)

    return result
