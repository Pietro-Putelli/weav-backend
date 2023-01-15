from django.db import models


class DeviceManager(models.Manager):
    def update_or_create(self, user, token):
        queryset = self.get_queryset().filter(user=user)

        if queryset.exists():
            queryset.update(token=token)
            return queryset.first()

        return self.create(user=user, token=token)