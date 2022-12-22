from django.db import models
from django.db.models.query_utils import Q


class UserChanceManager(models.Manager):
    def get_chances(self, user):
        return self.get_queryset().filter(Q(first=user) | Q(second=user))

    def get_chance(self, user):
        return self.get_chances(user).first()
