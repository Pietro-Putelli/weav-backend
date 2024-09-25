from datetime import timedelta, datetime
from functools import reduce
from itertools import groupby

import numpy

from business.models import Business
from insights.models import BusinessProfileVisit, BusinessLike, EventShare, EventRepost, \
    BusinessShare, BusinessRepost
from insights.serializers import OverviewInsight, LikeInsights, SummaryInsights, \
    RepostAndShareInsights
from moments.models import EventMoment
from users.models import User


class INSIGHT_TYPES:
    reposts = "reposts"
    shares = "shares"
    likes = "likes"
    visits = "visits"
    summary = "summary"


def parse_date(string_date):
    try:
        return datetime.strptime(string_date, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_dates(s_from_date, s_to_date):
    try:
        if isinstance(s_from_date, str):
            from_date = parse_date(s_from_date)
        else:
            from_date = s_from_date

        if isinstance(s_to_date, str):
            to_date = parse_date(s_to_date)
        else:
            to_date = s_to_date

        delta_date = to_date - from_date
        delta_days = delta_date.days

        return from_date, to_date, delta_days

    except ValueError:
        return None, None, None


def created_at_key(moment):
    return moment.get("created_at").strftime("%Y-%m-%d")


def group_by_date(items):
    result = {}

    for key, group in groupby(items, created_at_key):
        if result.get(key) is None:
            result[key] = list(group)
        else:
            result[key] += list(group)

    return result


def group_values(items, from_date, delta_days):
    result = group_by_date(items)

    values = [0] * delta_days

    for index in range(0, delta_days):
        date = from_date + timedelta(index)
        key_date = date.strftime("%Y-%m-%d")

        items = result.get(key_date)

        if items is not None:
            values[index] = len(items)

    return values


'''
    EVENT
'''


def add_share_to_event(user: User, event: EventMoment):
    event.add_share()

    EventShare.objects.create(user, event)


def add_repost_to_event(user: User, event: EventMoment):
    event.add_repost()

    EventRepost.objects.create(user, event)


'''
    BUSINESS
'''


def add_share_to_business(user: User, business: Business):
    BusinessShare.objects.create(user, business)


def add_repost_to_business(user: User, business: Business):
    business.add_repost()
    
    BusinessRepost.objects.create(user, business)


def add_business_profile_visits(user: User, business: Business):
    BusinessProfileVisit.objects.create(user, business)


def add_business_like(user: User, business: Business):
    BusinessLike.objects.create(user, business)


def remove_business_like(user: User, business: Business):
    BusinessLike.objects.filter(user=user, business=business).delete()


def create_reposts_or_shares_insight(mode, business, s_from_date, s_to_date):
    from_date, to_date, delta_days = parse_dates(s_from_date, s_to_date)

    if from_date is None:
        return None

    date_bounds = (from_date, to_date)

    business_model = BusinessRepost
    event_model = EventRepost

    if mode == "share":
        business_model = BusinessShare
        event_model = EventShare

    business_reposts = business_model.objects.get_between(business, *date_bounds).values(
        "created_at")
    # event_reposts = event_model.objects.get_between(event, *date_bounds).values("created_at")
    #
    # items = business_reposts.union(event_reposts)

    values = group_values(business_reposts, from_date, delta_days)

    business_reposts_count = business_reposts.count()
    # event_reposts_count = event_reposts.count()

    return RepostAndShareInsights(values, business_reposts_count, 0)


def create_reposts_insight(*args):
    return create_reposts_or_shares_insight("repost", *args)


def create_shares_insight(*args):
    return create_reposts_or_shares_insight("share", *args)


def create_profile_visit_insight(business, s_from_date, s_to_date):
    from_date, to_date, delta_days = parse_dates(s_from_date, s_to_date)

    visits = BusinessProfileVisit.objects.filter(business=business, created_at__gte=from_date,
                                                 created_at__lte=to_date).values("created_at")

    grouped_queryset = group_by_date(visits)
    insights = [0] * delta_days

    for index in range(0, delta_days):
        date = from_date + timedelta(index)
        key_date = date.strftime("%Y-%m-%d")

        visits = grouped_queryset.get(key_date)

        if visits is not None:
            insights[index] = len(visits)

    return {"values": insights}


def create_likes_insight(business, s_from_date, s_to_date):
    from_date, to_date, delta_days = parse_dates(s_from_date, s_to_date)

    likes = BusinessLike.objects.filter(business=business, created_at__gte=from_date,
                                        created_at__lte=to_date).values("created_at")

    users_count = BusinessLike.objects.get_between(business, from_date, to_date).count()

    grouped_queryset = group_by_date(likes)
    values = [0] * delta_days

    for index in range(0, delta_days):
        date = from_date + timedelta(index)
        key_date = date.strftime("%Y-%m-%d")

        likes = grouped_queryset.get(key_date)

        if likes is not None:
            values[index] = len(likes)

    return LikeInsights(values, users_count)


def get_total_reposts_count(*args):
    business_reposts = BusinessRepost.objects.get_between(*args).values("id").count()
    return business_reposts
    # event_reposts = EventRepost.objects.get_between(*args).values("id")
    # return business_reposts.union(event_reposts)


def get_total_shares_count(*args):
    business_shares = BusinessShare.objects.get_between(*args).values("id").count()
    return business_shares
    # event_shares = EventShare.objects.get_between(*args).values("id")
    # return business_shares.union(event_shares)


def get_total_likes_count(*args):
    return BusinessLike.objects.get_between(*args).count()


# Reposts -- Shares -- Likes -- Visits
def create_insights_overview(business, params):
    from_date = params.get("from")
    to_date = params.get("to")

    prev_from_date = params.get("prev_from")
    prev_to_date = params.get("prev_to")

    if None in [from_date, to_date, prev_from_date, prev_to_date]:
        return None

    overall_rank, category_rank = 0, 0

    # If the business is of type VENUE
    if business.location is not None:
        overall_rank = get_business_rank(business, from_date)
        category_rank = get_business_rank(business, from_date, True)

    # Reposts

    first_query_params = (business, from_date, to_date)
    second_query_params = (business, prev_from_date, prev_to_date)

    reposts_count = get_total_reposts_count(*first_query_params)
    prev_reposts_count = get_total_reposts_count(*second_query_params)

    delta_reposts = ((reposts_count - prev_reposts_count) / max(1, prev_reposts_count)) * 100

    # Shares

    shares_count = get_total_shares_count(*first_query_params)
    prev_shares_count = get_total_shares_count(*second_query_params)

    delta_shares = ((shares_count - prev_shares_count) / max(1, prev_shares_count)) * 100

    # Likes

    likes = get_total_likes_count(*first_query_params)
    prev_likes = get_total_likes_count(*second_query_params)

    delta_likes = ((likes - prev_likes) / max(1, prev_likes)) * 100

    # Profile visits

    profile_queryset = BusinessProfileVisit.objects

    visits = profile_queryset.get_count(*first_query_params)
    prev_visits = profile_queryset.get_count(*second_query_params)

    delta_visits = ((visits - prev_visits) / max(1, prev_visits)) * 100

    return OverviewInsight(overall_rank, category_rank, delta_reposts, delta_shares, delta_likes,
                           delta_visits)


def get_insight_values(*args):
    reposts = create_reposts_insight(*args).values
    shares = create_shares_insight(*args).values
    likes = create_likes_insight(*args).values

    return reposts, shares, likes


def get_total_interactions(business, from_date, to_date, reduced=False):
    params = (business, from_date, to_date)

    reposts, shares, likes = get_insight_values(*params)

    interactions = [reposts, shares, likes]
    total_interactions = list(numpy.sum(interactions, axis=0))

    if reduced:
        summed_interactions = reduce(lambda x, y: x + y, total_interactions)
        # Number type
        return summed_interactions

    # list type
    return total_interactions


def rank_value_key(item):
    return item.get("rank_value")


# Get business ranking in the last 7 days, following the hierarchy:
# 1. REPOSTS
# 2. SHARES
# 3. LIKES
def get_business_rank(my_business, s_from_date, use_category=False):
    from_date = parse_date(s_from_date)
    to_date = from_date + timedelta(days=7)

    businesses = Business.objects.get_by_place_id(my_business.location.place_id)
    remapped_businesses = []

    if use_category:
        businesses = businesses.filter(category=my_business.category)

    for business in businesses:
        params = (business, from_date, to_date)

        reposts_count, shares_count, likes_count = get_insight_values(*params)

        rank_value = 2 * reposts_count + 2 * shares_count + likes_count

        remapped_businesses.append({"rank_value": rank_value, "id": business.id})

    remapped_businesses.sort(key=rank_value_key, reverse=True)

    rank_index = None

    for index, business in enumerate(remapped_businesses):
        if my_business.id == business.get("id"):
            rank_index = index

    if rank_index is None:
        return None

    return rank_index + 1


def create_summary_insights(business, from_date, to_date):
    params = (business, from_date, to_date)

    reposts_count = get_total_reposts_count(*params)
    shares_count = get_total_shares_count(*params)
    likes_count = get_total_likes_count(*params)

    interactions = get_total_interactions(*params)

    summary = SummaryInsights(reposts_count, shares_count, likes_count, interactions)

    print(reposts_count, shares_count, likes_count, summary)

    return summary
