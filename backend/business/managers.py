from django.db import models
from django.db.models import Count


class BusinessManager(models.Manager):
    def only_approved(self):
        return self.get_queryset().filter(is_approved=True)

    def get_or_none(self, id):
        try:
            return self.get_queryset().get(id=id)
        except self.model.DoesNotExists:
            return None

    def get_by_place_id(self, place_id):
        return self.only_approved().filter(location__place_id=place_id)

    def get_business_rank(self, place_id, category):
        return (
            self.only_approved()
                .filter(location__place_id=place_id, category__id=category)
                .distinct()
                .annotate(likes_count=Count("likes"))
                .order_by("-likes_count", "id")[:10]
        )
