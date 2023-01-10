from django.apps import AppConfig
from django.db.models.signals import post_save


class BusinessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'business'

    def ready(self):
        from .signals import rename_business_dir, create_auth_token

        post_save.connect(rename_business_dir, sender="business.Business")
        post_save.connect(create_auth_token, sender='business.Business')
