from django.db import models
from concurrency.fields import IntegerVersionField


class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at", "updated_at"]


class DateOnlyModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class ConcurrentModel(TimestampModel):
    version = IntegerVersionField()

    class Meta:
        abstract = True
