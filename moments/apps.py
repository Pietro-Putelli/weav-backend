from django.apps import AppConfig
from django.db.models.signals import post_delete


class MomentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moments'

    def ready(self):
        from . import signals
