from django.db import models


class DeviceManager(models.Manager):
    def update_or_create(self, user, os_type, token=None):
        queryset = self.get_queryset().filter(user=user)

        if queryset.exists() and token is not None:
            queryset.update(token=token)
            return queryset.first()

        return self.create(user=user, os_type=os_type, token=token)

    def login(self, user):
        self.get_queryset().filter(user=user).update(is_logged=True)

    def logout(self, user):
        self.get_queryset().filter(user=user).update(is_logged=False, is_business=False)
