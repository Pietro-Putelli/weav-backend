from django.db import models
from services.date import today_date, get_today_day
from django.utils import timezone
from datetime import datetime, timedelta


class BusinessInsightsManager(models.Manager):
    def get_between(self, business, from_date, to_date):
        return self.get_queryset().filter(
            business=business, created_at__gte=from_date, created_at__lte=to_date
        )

    def create(self, user, business):
        today = get_today_day()

        insights = self.get_queryset().filter(
            created_at__day=today, user=user, business=business
        )

        if not insights.exists():
            return super().create(user=user, business=business)

        return None

    def get_count(self, business, from_date, to_date):
        return self.get_between(business, from_date, to_date).count()

    def get_this_week_count(self, business):
        today = today_date()
        from_date = today - timedelta(days=today.weekday())
        to_date = from_date + timedelta(days=6)

        from_date = timezone.make_aware(
            datetime.combine(from_date, datetime.min.time())
        )
        to_date = timezone.make_aware(datetime.combine(to_date, datetime.max.time()))

        return self.get_between(business, from_date, to_date).count()


class EventInsightManager(models.Manager):
    def get_between(self, event, from_date, to_date):
        return self.get_queryset().filter(
            event=event, created_at__gte=from_date, created_at__lte=to_date
        )

    def create(self, user, event):
        today = get_today_day()

        insights = self.get_queryset().filter(
            created_at__day=today, user=user, event=event
        )

        if not insights.exists():
            return super().create(user=user, event=event)

        return None

    def get_count(self, event, from_date, to_date):
        return self.get_between(event, from_date, to_date).count()
