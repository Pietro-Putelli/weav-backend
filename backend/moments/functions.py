from django.db.models import FloatField, Case, When
from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.db.models.functions import Coalesce
from django.contrib.gis.measure import Distance as MeasureDistance
from django.db.models.query_utils import Q
from django.utils import timezone

from core.constants import SEARCH_RADIUS_NOT_IN_CITY
from moments.models import EventMoment, UserMoment
from services.utils import get_point_coordinate


def parse_user_data(request):
    data = request.data or request.query_params

    coordinate = data.get("coordinate", None)

    if coordinate:
        coordinate = get_point_coordinate(coordinate)

    place_id = data.get("place_id")
    offset = data.get("offset")
    up_offset = offset + 8

    return coordinate, place_id, offset, up_offset


def get_user_moments_by(request):
    coordinate, place_id, offset, up_offset = parse_user_data(request)

    user = request.user
    now = timezone.now()

    blocked_users = user.profile.blocked_users.all()

    queryset = UserMoment.objects.filter(end_at__gte=now).exclude(
        Q(user__in=blocked_users)
    )

    if place_id:
        queryset = queryset.filter(location__place_id=place_id)

    if coordinate:
        queryset = (
            queryset.filter(
                location__coordinate__distance_lte=(
                    coordinate,
                    MeasureDistance(m=SEARCH_RADIUS_NOT_IN_CITY),
                )
            )
            .annotate(distance=GeoDistance("location__coordinate", coordinate))
            .order_by("distance")
        )

    queryset = queryset.filter(~Q(user__blocked_users__in=[user.profile])).order_by(
        "-created_at"
    )

    return queryset[offset:up_offset]


# Distances are in meters


def get_event_moments_by(data):
    coordinate = data.get("coordinate")

    place_id = data.get("place_id")
    offset = data.get("offset")
    up_offset = offset + 8

    queryset = EventMoment.objects.get_approved()

    if place_id:
        queryset = queryset.filter(
            Q(business__location__place_id=place_id) | Q(location__place_id=place_id)
        )

    if coordinate and not place_id:
        queryset = (
            queryset.filter(
                Q(
                    Q(
                        business__location__coordinate__distance_lte=(
                            coordinate,
                            MeasureDistance(m=SEARCH_RADIUS_NOT_IN_CITY),
                        )
                    )
                    | Q(
                        location__coordinate__distance_lte=(
                            coordinate,
                            MeasureDistance(m=SEARCH_RADIUS_NOT_IN_CITY),
                        )
                    )
                )
            )
            .annotate(
                distance=GeoDistance(
                    Coalesce("business__location__coordinate", "location__coordinate"),
                    coordinate,
                )
            )
            .order_by("distance")
        )

    if place_id:
        queryset = queryset.annotate(
            distance=Case(
                When(
                    has_activity=True,
                    then=GeoDistance(
                        Coalesce(
                            "business__location__coordinate", "location__coordinate"
                        ),
                        coordinate,
                    ),
                ),
                default=None,
                output_field=FloatField(),
            )
        )

    queryset = queryset.order_by("date")

    return queryset[offset:up_offset]
