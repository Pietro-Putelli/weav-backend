from django.contrib.gis.db.models.functions import Distance as GeoDistance
from django.contrib.gis.measure import Distance as MeasureDistance
from django.db.models import Count
from django.db.models import Exists, OuterRef
from django.db.models.query_utils import Q

from business.categories import VenueCategories, VenueTypes
from business.models import Business
from business.query_expressions import (
    get_timetable_params,
    get_tonight_timetable_params,
)
from core.constants import SEARCH_RADIUS_NOT_IN_CITY
from core.querylimits import QueryLimits
from services.date import (
    get_date_for_search,
    get_yesterday_and_today,
    get_midnight_for_search,
)
from spots.models import Spot


def get_businesses_nearby(data):
    date = data.get("date")
    user_date = get_date_for_search(date)

    place_id = data.get("place_id", None)
    user_position = data.get("coordinate")

    experience_type = data.get("type")

    categories = data.get("categories", [])
    amenities = data.get("amenities", [])
    price_target = data.get("price_target")

    closed_too = data.get("closed_too")

    offset = data.get("offset")
    up_offset = offset + QueryLimits.BUSINESS_LIST

    is_city = place_id is not None

    queryset = Business.objects.only_approved().filter(timetable__isnull=False)

    if is_city:
        queryset = queryset.filter(location__place_id=place_id)
    else:
        queryset = queryset.filter(
            location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=SEARCH_RADIUS_NOT_IN_CITY),
            )
        )

    queryset = queryset.annotate(
        distance=GeoDistance("location__coordinate", user_position),
        likes_count=Count("likes"),
    )

    if len(categories) > 0 or len(amenities) > 0:
        queryset = queryset.filter(
            Q(categories__id__in=categories)
            | Q(amenities__id__in=amenities)
            | Q(category__id__in=categories)
        )

    if price_target:
        queryset = queryset.filter(price_target=price_target)

    order_by_params = ("distance", "-likes_count", "id")
    categories = []

    is_tonight = None

    if experience_type is not None:
        is_tonight = VenueTypes[experience_type] == "tonight"

        if is_tonight or VenueTypes[experience_type] == "populars":
            order_by_params = ("-likes_count", "distance", "id")

        if is_tonight:
            categories = VenueCategories.TONIGHT

        elif VenueTypes[experience_type] == "to_eat":
            categories = VenueCategories.TO_EAT

        elif VenueTypes[experience_type] == "aperitif":
            categories = VenueCategories.APERITIF

        elif VenueTypes[experience_type] == "café":
            categories = VenueCategories.CAFE

    if len(categories) > 0:
        queryset = queryset.filter(
            Q(categories__en__in=categories) | Q(category__en__in=categories)
        )

    if closed_too:
        queryset = queryset.order_by(*order_by_params)
        return queryset[offset:up_offset]

    # Start time selection

    [yesterday, today] = get_yesterday_and_today(date, offset_midnight=True)

    business_open_yesterday_query = {f"timetable__{yesterday}__len__gte": 2}
    business_open_today_query = {f"timetable__{today}__len__gte": 2}

    # If tonight is selected then we need to filter all businesses open after 20:00

    if is_tonight:
        [first_from, first_to, second_from, second_to] = get_tonight_timetable_params(
            today
        )

        queryset = queryset.filter(
            Q(Q(**first_from) & Q(**first_to)) | Q(Q(**second_from) & Q(**second_to))
        ).order_by(*order_by_params)

        return queryset[offset:up_offset]

    next_day_midnight = get_midnight_for_search()

    # All businesses that are open yesterday

    yesterday_queryset = queryset.filter(**business_open_yesterday_query)

    # All businesses that are open today

    today_queryset = queryset.filter(**business_open_today_query)

    # All businesses that are open at the time of the request

    """
        start_date - user_date > 0
        end_date - user_date > 0
        
        If both are verified, add one day to user_date
    """

    deltas, timetable_query, query_conditions = get_timetable_params(
        today, yesterday, user_date
    )

    [
        yesterday_first_sc_delta,
        yesterday_first_ec_delta,
        yesterday_second_sc_delta,
        yesterday_second_ec_delta,
        today_first_sc_delta,
        today_first_ec_delta,
        today_second_sc_delta,
        today_second_ec_delta,
    ] = deltas

    [
        yesterday_first_from,
        yesterday_first_to,
        yesterday_second_from,
        yesterday_second_to,
        today_first_from,
        today_first_to,
        today_second_from,
        today_second_to,
    ] = timetable_query

    [
        yesterday_first_query_condition,
        yesterday_second_query_condition,
        today_first_query_condition,
        today_second_query_condition,
    ] = query_conditions

    yesterday_first_queryset = (
        yesterday_queryset.filter()
        .annotate(
            yesterday_first_sc_delta=yesterday_first_sc_delta,
            yesterday_first_ec_delta=yesterday_first_ec_delta,
        )
        .annotate(**yesterday_first_query_condition)
        .filter(user_date__gte=next_day_midnight)
        .filter(Q(**yesterday_first_from) & Q(**yesterday_first_to))
    )

    today_first_queryset = (
        today_queryset.filter()
        .annotate(
            today_first_sc_delta=today_first_sc_delta,
            today_first_ec_delta=today_first_ec_delta,
        )
        .annotate(**today_first_query_condition)
        .filter(Q(**today_first_from) & Q(**today_first_to))
    )

    timetable_len_check_yesterday = {f"timetable__{yesterday}__len__gt": 2}
    timetable_len_check_today = {f"timetable__{today}__len__gt": 2}

    yesterday_second_queryset = (
        yesterday_queryset.filter(**timetable_len_check_yesterday)
        .annotate(
            yesterday_second_sc_delta=yesterday_second_sc_delta,
            yesterday_second_ec_delta=yesterday_second_ec_delta,
        )
        .annotate(**yesterday_second_query_condition)
        .filter(user_date__gte=next_day_midnight)
        .filter(Q(**yesterday_second_from) & Q(**yesterday_second_to))
    )

    today_second_queryset = (
        today_queryset.filter(**timetable_len_check_today)
        .annotate(
            today_second_sc_delta=today_second_sc_delta,
            today_second_ec_delta=today_second_ec_delta,
        )
        .annotate(**today_second_query_condition)
        .filter(Q(**today_second_from) & Q(**today_second_to))
    )

    first_queryset = yesterday_first_queryset | today_first_queryset

    second_queryset = today_second_queryset | yesterday_second_queryset

    queryset = first_queryset | second_queryset

    queryset = queryset.order_by(*order_by_params)

    return queryset[offset:up_offset]


def get_business_rank_value(business):
    location = business.location
    category = business.category

    if category is None:
        return None

    queryset = Business.objects.get_business_rank(location.place_id, category.id)

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
    up_offset = offset + QueryLimits.SEARCH_BUSINESS_LIMIT

    return (
        Business.objects.only_approved()
        .filter(
            location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=5000),
            ),
        )
        .annotate(distance=GeoDistance("location__coordinate", user_position))
        .order_by("distance")[offset:up_offset]
    )


def get_overall_business_rank(business):
    queryset = Business.objects.get_by_place_id(business.location.place_id)

    rank_index = 0

    for index, buss in enumerate(queryset):
        if buss.id == business.id:
            rank_index = index + 1

    return rank_index


def get_businesses_for_spot(data):
    place_id = data.get("place_id", None)
    user_position = data.get("coordinate")

    offset = data.get("offset")
    up_offset = offset + 8

    is_city = place_id is not None

    spots_exist = Spot.objects.filter(business=OuterRef("pk"))

    queryset = (
        Business.objects.only_approved()
        .annotate(has_spots=Exists(spots_exist))
        .filter(has_spots=True)
    )

    if is_city:
        queryset = queryset.filter(location__place_id=place_id)
    else:
        queryset = queryset.filter(
            location__coordinate__distance_lte=(
                user_position,
                MeasureDistance(m=SEARCH_RADIUS_NOT_IN_CITY),
            )
        )

    queryset = queryset.annotate(
        distance=GeoDistance("location__coordinate", user_position)
    )

    queryset = queryset.order_by("distance")[offset:up_offset]

    return queryset
