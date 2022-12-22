from django.db import models
from servicies.date import date_from
from django.db.models import Sum


class UserMomentManager(models.Manager):
    # Get all users moments in 24 hours, so only the active ones.
    def get_today_moments(self):
        return self.get_queryset().filter(created_at__gte=date_from(1))

    def get_moments_where_im_tagged(self, user):
        return self.get_today_moments().filter(users_tag__in=[user])

    def get_moments_where_im_tagged_count(self, user):
        return self.get_moments_where_im_tagged(user).count()


class EventMomentManager(models.Manager):
    def _current_moment_queryset(self, business):
        return self.get_queryset().filter(business=business, created_at__gte=date_from(10))

    def get_current(self, business):
        return self._current_moment_queryset(business).first()

    def update_current_business(self, business, **kwargs):
        return self._current_moment_queryset(business).update(**kwargs)

    def delete_current(self, business):
        return self._current_moment_queryset(business).delete()

    def delete_current_if_has_no_slices(self, business):
        from moments.models import EventMomentSlice

        moment = self.get_current(business)
        slices = EventMomentSlice.objects.get_current_moment_slices(moment)

        if slices.count() == 0:
            self.delete_current(business)


class EventMomentSliceManager(models.Manager):
    def get_current_moment_slices(self, moment):
        return self.get_queryset().filter(moment=moment, created_at__gte=date_from(10))

    def get_slices_between(self, business, from_date, to_date):
        return self.get_queryset().filter(moment__business=business,
                                          created_at__gte=from_date,
                                          created_at__lte=to_date)

    def get_cover(self, moment):
        return self.get_queryset().filter(moment=moment).last()
