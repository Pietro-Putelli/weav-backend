from django.db import models


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
