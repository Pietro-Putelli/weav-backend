from django.apps import AppConfig
from django.db.models.signals import post_save


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from .signals import create_auth_token

        post_save.connect(create_auth_token, sender='users.User')
