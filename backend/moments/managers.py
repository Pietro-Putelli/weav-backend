from django.db import models

from services.date import date_from


class UserMomentManager(models.Manager):
    # Get all users moments in 24 hours, so only the active ones.
    def get_today_moments(self):
        return self.get_queryset().filter(created_at__gte=date_from(1))

    def get_moments_where_im_tagged(self, user):
        return self.get_today_moments().filter(participants__in=[user])


class EventMomentManager(models.Manager):
    def get_approved(self):
        return self.get_queryset().filter(business__is_approved=True)

    def get_mine(self, profile):
        return self.get_approved().filter(participants__in=[profile])
