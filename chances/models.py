from django.db import models
from .managers import UserChanceManager


class Chance(models.Model):
    first = models.ForeignKey("users.User", related_name="%(app_label)s_%(class)s_first_user",
                              on_delete=models.CASCADE)
    second = models.ForeignKey("users.User", related_name="%(app_label)s_%(class)s_second_user",
                               on_delete=models.CASCADE)

    class Meta:
        abstract = True


class UserChance(Chance):
    objects = UserChanceManager()


class EventChance(Chance):
    event = models.ForeignKey("moments.EventMoment",
                              related_name="%(app_label)s_%(class)s_chance_event",
                              on_delete=models.CASCADE)
