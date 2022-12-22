from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.contrib.gis.measure import Distance as MeasureDistance
from django.db.models import Count
from django.db.models.query_utils import Q

from business.models import Business
from core.querylimits import QueryLimits
from servicies.querylimits import SEARCH_BUSINESS_LIMIT


def get_businesses_nearby(data):
    user_position = data.get("coordinate")

    # FILTERS
    categories = data.get("categories", [])
    amenities = data.get("amenities", [])
    price_target = data.get("price_target")

    is_city = data.get("is_city")
    place_id = data.get("place_id")

    offset = data.get("offset")
    up_offset = offset + QueryLimits.BUSINESS_LIST

    queryset = Business.objects.filter(is_approved=True)

    if len(categories) > 0 or len(amenities) > 0:
        filter_query = Q(categories__id__in=categories) | Q(amenities__id__in=amenities) | Q(
            category__id__in=categories)

        queryset = queryset.filter(filter_query)

    if price_target:
        queryset = queryset.filter(price_target=price_target)

    if not is_city:
        queryset = queryset.filter(
            location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=1000),
            ),
        ).annotate(
            distance=GeoDistance("location__coordinate", user_position)
        ).annotate(likes_count=Count("likes")).order_by("distance", "-likes_count")
    else:
        queryset = queryset.filter(location__place_id=place_id).annotate(
            distance=GeoDistance("location__coordinate", user_position)
        ).annotate(likes_count=Count("likes")).order_by("-likes_count", "distance")

    return queryset[offset:up_offset]


def get_business_rank_value(business):
    location = business.location

    if business.categories.count() < 1:
        return None

    category = business.category

    queryset = Business.objects.get_by_place_id(location.place_id).filter(
        category=category).annotate(likes_count=Count("likes")).order_by("-likes_count")

    index = 0
    rank_value = None

    for query in list(queryset):
        if query.id == business.id:
            rank_value = index
        index += 1

        if index == 10:
            break

    if rank_value is not None:
        return rank_value + 1

    return None


# Used when the searching value is empty
def get_nearest_businesses(user_position, offset):
    up_offset = offset + SEARCH_BUSINESS_LIMIT

    return Business.objects.filter(
        location__coordinate__distance_lte=(
            user_position,
            MeasureDistance(m=5000),
        ),
    ).annotate(
        distance=GeoDistance("location__coordinate", user_position)
    ).order_by("distance")[offset:up_offset]


def get_overall_business_rank(business):
    queryset = Business.objects.get_by_place_id(business.location.place_id)

    rank_index = 0

    for index, buss in enumerate(queryset):
        if buss.id == business.id:
            rank_index = index + 1

    return rank_index
