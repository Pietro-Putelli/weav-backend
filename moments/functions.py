from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.contrib.gis.measure import Distance as MeasureDistance
from django.db.models import OuterRef
from django.db.models.query_utils import Q
from django.utils import timezone

from core.querylimits import QueryLimits
from moments.models import EventMoment, UserMoment, EventMomentSlice
from servicies.date import date_from
from servicies.utils import get_point_coordinate

MAX_MOMENT_RADIUS = 1000


def parse_user_data(data):
    coordinate = data.get("coordinate")
    user_position = get_point_coordinate(coordinate)

    place_id = data.get("place_id")
    search_type = data.get("search_type")
    offset = data.get("offset", 0)

    return user_position, place_id, search_type, offset


def get_user_moments_by(request):
    user_position, place_id, search_type, offset = parse_user_data(
        request.data)

    user = request.user

    up_offset = offset + 8

    now = timezone.now()

    queryset = UserMoment.objects.filter(end_at__gte=now).exclude(
        Q(user__in=request.user.profile.blocked_users.all())
    )

    if search_type == "nearby":
        queryset = queryset.filter(
            location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=MAX_MOMENT_RADIUS),
            ),
        ).annotate(distance=GeoDistance("location__coordinate", user_position)).order_by("distance")

    else:
        queryset = queryset.filter(location__place_id=place_id).order_by(
            "-created_at"
        )

    queryset = queryset.filter(~Q(user__profile__blocked_users__in=[user]))

    return queryset[offset:up_offset]


def get_event_moments_by(request):
    user_position, place_id, search_type, offset = parse_user_data(
        request.data)

    up_offset = offset + QueryLimits.EVENT_MOMENTS_LIST

    queryset = EventMoment.objects.filter(business__is_approved=True,
                                          created_at__gte=date_from(200))

    if search_type == "nearby":
        queryset = queryset.filter(
            business__location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=MAX_MOMENT_RADIUS),
            ),
        ).annotate(distance=GeoDistance("location__coordinate", user_position)).order_by("distance")

    else:
        queryset = queryset.filter(Q(business__location__place_id=place_id) | Q(
            location__place_id=place_id))

        subquery = EventMomentSlice.objects.filter(moment=OuterRef("pk"))

        queryset = queryset.annotate(
            last_slice_created_at=subquery.values("created_at")[:1]).order_by(
            "-last_slice_created_at")

    return queryset[offset:up_offset]
