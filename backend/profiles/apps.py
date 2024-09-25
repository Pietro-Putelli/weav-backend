from django.apps import AppConfig
from django.db.models.signals import post_save


class ProfilesConfig(AppConfig):
    name = 'profiles'

    def ready(self):
        from . import signals
