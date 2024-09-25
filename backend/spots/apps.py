from django.apps import AppConfig


class SpotsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "spots"

    def ready(self):
        from . import signals
