from datetime import datetime, timedelta

import pytz
from django.utils import timezone


def utc_to_timezone(date, timezone):
    tz = pytz.timezone(timezone)
    return date.replace(tzinfo=pytz.utc).astimezone(tz)


def day_date_format(date, timezone):
    string_date = (
        utc_to_timezone(date, timezone).strftime("%Y-%m-%d %H:%M:%S").partition(".")[0]
    )
    return datetime.strptime(string_date, "%Y-%m-%d %H:%M:%S").strftime(
        format="%Y-%m-%d"
    )


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
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def get_date_tz_aware(date):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(date, tz, True).date()
