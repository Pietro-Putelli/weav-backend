from django.apps import AppConfig
from django.db.models.signals import post_save


class ProfilesConfig(AppConfig):
    name = 'profiles'

    def ready(self):
        from .signals import create_picture_placeholder
        post_save.connect(create_picture_placeholder, sender='profiles.UserProfile')
