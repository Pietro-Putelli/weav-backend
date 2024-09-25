from django.contrib import admin
from django.utils import timezone
from django.utils.text import Truncator
from services.date import get_date_tz_aware
from datetime import datetime, timedelta
from moments.models import EventMoment, UserMoment


class MomentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "text_content",
        "has_source",
        "has_business",
        "has_url",
        "has_location",
    )
    readonly_fields = ("uuid",)

    @admin.action(description="Delete expired moments")
    def delete_expired_moments(_, __, queryset):
        for moment in queryset:
            # check if end_at is expired
            if moment.end_at < timezone.now():
                moment.delete()

    actions = [delete_expired_moments]

    @admin.display(
        boolean=True,
        description="source",
    )
    def has_source(self, moment):
        return bool(moment.source)

    def text_content(self, moment):
        return Truncator(moment.content).chars(50)

    @admin.display(
        boolean=True,
        description="business",
    )
    def has_business(self, moment):
        return bool(moment.business_tag)

    @admin.display(
        boolean=True,
        description="url",
    )
    def has_url(self, moment):
        return bool(moment.url_tag)

    @admin.display(
        boolean=True,
        description="location",
    )
    def has_location(self, moment):
        return bool(moment.location_tag)


@admin.register(UserMoment)
class UserMomentAdmin(MomentAdmin):
    list_display = MomentAdmin.list_display


@admin.register(EventMoment)
class EventMomentAdmin(admin.ModelAdmin):
    list_display = ("title", "business", "id", "date", "is_periodic", "has_activity")

    @admin.action(description="Delete expired events")
    def delete_expired_events(_, __, queryset):
        for event in queryset:
            date = event.date

            if date is None:
                continue

            start_time = event.time
            end_time = event.end_time

            if end_time < start_time:
                date += timedelta(days=1)

            event_datetime_naive = datetime.combine(date, end_time)
            event_datetime_aware = get_date_tz_aware(event_datetime_naive)

            # Check if event is not periodic and then check if it's expired
            if event.periodic_day is None and event_datetime_aware < timezone.now():
                event.delete()

    actions = [delete_expired_events]

    @admin.display(
        boolean=True,
        description="periodic",
    )
    def is_periodic(self, event):
        return event.periodic_day is not None

    @admin.display(
        boolean=True,
        description="has activity",
    )
    def has_activity(self, event):
        return event.has_activity
