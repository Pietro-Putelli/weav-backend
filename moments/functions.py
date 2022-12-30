from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.contrib.gis.measure import Distance as MeasureDistance
from django.db.models import OuterRef
from django.db.models.query_utils import Q
from django.utils import timezone

from moments.models import EventMoment, UserMoment, EventMomentSlice
from servicies.date import date_from
from servicies.utils import get_point_coordinate, cast_to_int

MAX_MOMENT_RADIUS = 1000


def parse_user_data(request):
    data = request.data or request.query_params

    coordinate = data.get("coordinate", None)

    if coordinate:
        coordinate = get_point_coordinate(coordinate)

    place_id = data.get("place_id")
    offset = cast_to_int(data.get("offset", 0))
    up_offset = offset + 8

    return coordinate, place_id, offset, up_offset


def get_user_moments_by(request):
    coordinate, place_id, offset, up_offset = parse_user_data(request)

    user = request.user
    now = timezone.now()

    queryset = UserMoment.objects.filter(end_at__gte=now).exclude(
        Q(user__in=request.user.profile.blocked_users.all())
    )

    if place_id:
        queryset = queryset.filter(location__place_id=place_id).order_by("-created_at")

    if coordinate:
        queryset = queryset.filter(
            location__coordinate__distance_lte=(
                coordinate, MeasureDistance(m=MAX_MOMENT_RADIUS)
            )
        ).annotate(
            distance=GeoDistance("location__coordinate", coordinate)
        ).order_by("distance")

    queryset = queryset.filter(~Q(user__profile__blocked_users__in=[user]))

    return queryset[offset:up_offset]


def get_event_moments_by(request):
    coordinate, place_id, offset, up_offset = parse_user_data(request)

    queryset = EventMoment.objects.get_approved().filter(created_at__gte=date_from(200))

    if place_id:
        queryset = queryset.filter(
            Q(business__location__place_id=place_id) | Q(location__place_id=place_id))

    if coordinate:
        queryset = queryset.filter(
            business__location__coordinate__distance_lte=(
                coordinate,
                MeasureDistance(m=MAX_MOMENT_RADIUS),
            ),
        ).annotate(
            distance=GeoDistance("location__coordinate", coordinate)
        ).order_by("distance")

    subquery = EventMomentSlice.objects.filter(moment=OuterRef("pk"))

    queryset = queryset.annotate(
        last_slice_created_at=subquery.values("created_at")[:1]).order_by("-last_slice_created_at")

    return queryset[offset:up_offset]
