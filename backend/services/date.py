from datetime import datetime, timedelta, time

import pytz
from django.utils import timezone

utc_timezone = pytz.timezone("UTC")


def get_current_date():
    return timezone.now()


def date_from(days):
    return get_current_date() - timedelta(days=days)


def today_date():
    return datetime.today().today()


def get_today_day():
    return today_date().day


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def get_date_tz_aware(date):
    return timezone.make_aware(date, timezone.get_default_timezone())


# Use to get date for querying businesses based on timetable
def get_date_for_search(date):
    return datetime(2023, 1, 1, date.hour, date.minute, tzinfo=utc_timezone)


def get_midnight_for_search():
    return datetime(2023, 1, 2, 0, 0, tzinfo=utc_timezone)


def get_tonight_threshold_for_search():
    return datetime(2023, 1, 1, 23, 0, tzinfo=utc_timezone)


def get_yesterday_and_today(date, offset_midnight=False):
    if offset_midnight:
        midnight = time(0, 0)

        if date.time() > midnight:
            date = date - timedelta(days=1)

    today = date.strftime("%a").lower()
    yesterday = (date - timedelta(days=1)).strftime("%a").lower()

    return [yesterday, today]
