from django.db.models import ExpressionWrapper, IntegerField, F, Case, When, F, DateTimeField, Count
from django.db.models.query_utils import Q
from django.db.models.functions import Extract
from datetime import timedelta
from services.date import get_tonight_threshold_for_search


def get_date_delta_expression(timetable_id, user_date):
    # Extract the hour and minute components from the timetable_id
    timetable_hour = Extract(F(timetable_id), "hour")
    timetable_minute = Extract(F(timetable_id), "minute")
    
    # Extract the hour and minute components from the user_date
    user_hour = Extract(user_date, "hour")
    user_minute = Extract(user_date, "minute")
    
    # Calculate the time difference in minutes
    minute_difference = (timetable_hour - user_hour) * 60 + (timetable_minute - user_minute)
    
    # Convert minutes to hours
    hour_difference = ExpressionWrapper(minute_difference / 60, output_field=IntegerField())
    
    return hour_difference

def get_timetable_params(today, yesterday, user_date):
    yesterday_timetable_0 = f"timetable__{yesterday}__0"
    yesterday_timetable_1 = f"timetable__{yesterday}__1"
    yesterday_timetable_2 = f"timetable__{yesterday}__2"
    yesterday_timetable_3 = f"timetable__{yesterday}__3"

    today_timetable_0 = f"timetable__{today}__0"
    today_timetable_1 = f"timetable__{today}__1"
    today_timetable_2 = f"timetable__{today}__2"
    today_timetable_3 = f"timetable__{today}__3"

    yesterday_first_sc_delta = get_date_delta_expression(yesterday_timetable_0, user_date)
    yesterday_first_ec_delta = get_date_delta_expression(yesterday_timetable_1, user_date)
    yesterday_second_sc_delta = get_date_delta_expression(yesterday_timetable_2, user_date)
    yesterday_second_ec_delta = get_date_delta_expression(yesterday_timetable_3, user_date)

    today_first_sc_delta = get_date_delta_expression(today_timetable_0, user_date)
    today_first_ec_delta = get_date_delta_expression(today_timetable_1, user_date)
    today_second_sc_delta = get_date_delta_expression(today_timetable_2, user_date)
    today_second_ec_delta = get_date_delta_expression(today_timetable_3, user_date)

    yesterday_first_from = {f"{yesterday_timetable_0}__lte": F("user_date")}
    yesterday_first_to = {f"{yesterday_timetable_1}__gte": F("user_date")}

    yesterday_second_from = {f"{yesterday_timetable_2}__lte": F("user_date")}
    yesterday_second_to = {f"{yesterday_timetable_3}__gte": F("user_date")}

    today_first_from = {f"{today_timetable_0}__lte": F("user_date")}
    today_first_to = {f"{today_timetable_1}__gte": F("user_date")}

    today_second_from = {f"{today_timetable_2}__lte": F("user_date")}
    today_second_to = {f"{today_timetable_3}__gte": F("user_date")}

    user_date_adjusted = user_date + timedelta(1)

    yesterday_first_query_condition = {"user_date": Case(
        When(Q(yesterday_first_sc_delta__gt=0) & Q(yesterday_first_ec_delta__gt=0),
             then=user_date_adjusted), default=user_date, output_field=DateTimeField(),
    )}

    yesterday_second_query_condition = {"user_date": Case(
        When(Q(yesterday_second_sc_delta__gt=0) & Q(yesterday_second_sc_delta__gt=0),
             then=user_date_adjusted), default=user_date, output_field=DateTimeField()
    )}

    today_first_query_condition = {"user_date": Case(
        When(Q(today_first_sc_delta__gt=0) & Q(today_first_ec_delta__gt=0),
             then=user_date_adjusted), default=user_date, output_field=DateTimeField()
    )}

    today_second_query_condition = {"user_date": Case(
        When(Q(today_second_sc_delta__gt=0) & Q(today_second_ec_delta__gt=0),
             then=user_date_adjusted), default=user_date, output_field=DateTimeField()
    )}

    deltas = [yesterday_first_sc_delta, yesterday_first_ec_delta, yesterday_second_sc_delta,
              yesterday_second_ec_delta, today_first_sc_delta, today_first_ec_delta,
              today_second_sc_delta, today_second_ec_delta]

    timetable_query = [yesterday_first_from, yesterday_first_to, yesterday_second_from,
                       yesterday_second_to, today_first_from, today_first_to, today_second_from,
                       today_second_to]

    query_conditions = [yesterday_first_query_condition, yesterday_second_query_condition,
                        today_first_query_condition, today_second_query_condition]

    return deltas, timetable_query, query_conditions


def get_tonight_timetable_params(today):
    timetable_0 = f"timetable__{today}__0"
    timetable_1 = f"timetable__{today}__1"
    timetable_2 = f"timetable__{today}__2"
    timetable_3 = f"timetable__{today}__3"

    tonight_threshold_date = get_tonight_threshold_for_search()

    first_from = {f"{timetable_0}__lte": tonight_threshold_date}
    first_to = {f"{timetable_1}__gte": tonight_threshold_date}

    second_from = {f"{timetable_2}__lte": tonight_threshold_date}
    second_to = {f"{timetable_3}__gte": tonight_threshold_date}

    return [first_from, first_to, second_from, second_to]
