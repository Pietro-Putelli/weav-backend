from datetime import datetime, timedelta
from itertools import groupby

from django.db.models.query_utils import Q

from django.db.models import FloatField, Case, When
from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.db.models.functions import Coalesce
from django.db.models.query_utils import Q
from services.date import get_current_date
from moments.models import EventMoment
from profiles.models import UserFriend


def get_event_participants(event_id, user, offset, limit):
    from .serializers import EventParticipantSerializer

    try:
        event = EventMoment.objects.get(uuid=event_id)
    except EventMoment.DoesNotExist:
        return None

    participants = event.participants.all()

    friends = UserFriend.objects.filter(
        Q(user=user, friend__in=participants) | Q(friend=user, user__in=participants)
    )

    count = friends.count()
    friends = friends[offset : limit + offset]

    users = []

    for friend in friends:
        if friend.user == user:
            users.append(friend.friend)
        else:
            users.append(friend.user)

    return EventParticipantSerializer({"users": users, "count": count}).data


def get_grouped_my_events(profile):
    from moments.serializers import ShortEventMomentSerializer

    def event_key(event):
        return ShortEventMomentSerializer(event, context={"user": profile}).data

    lower_bound = datetime.now() - timedelta(1)
    upper_bound = lower_bound + timedelta(8)

    events = EventMoment.objects.filter(
        participants__in=[profile], date__gte=lower_bound, date__lte=upper_bound
    )

    result = {}

    for key, group in groupby(events, lambda event: event.date):
        new_key = key.strftime("%Y-%m-%d")

        if result.get(new_key) is None:
            new_group = map(event_key, list(group))
            result[new_key] = list(new_group)

    return result


def get_my_events_using_position(data, profile):
    queryset = EventMoment.objects.get_mine(profile)

    coordinate = data.get("coordinate")
    offset = data.get("offset")

    queryset = queryset.annotate(
        distance=Case(
            When(
                has_activity=True,
                then=GeoDistance(
                    Coalesce("business__location__coordinate", "location__coordinate"),
                    coordinate,
                ),
            ),
            default=None,
            output_field=FloatField(),
        )
    )

    queryset = queryset.order_by("date")

    return queryset[offset : offset + 8]


"""
    Use to get events that will start in 30 minutes
"""


def get_my_events_info(profile):
    events = EventMoment.objects.get_mine(profile)

    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y-%m-%d")
    date = datetime.strptime(formatted_date, "%Y-%m-%d")

    events = events.filter(date__lte=date)

    count = events.count()

    return {"myEventsCount": count}
