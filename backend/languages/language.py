import os
import json
from django.conf import settings


def get_language_content(instance):
    from users.models import User
    from business.models import Business

    language = "en"

    if isinstance(instance, int):
        user = User.objects.filter(id=instance)

        if user.exists():
            user = user.first()
            language = user.language
    elif isinstance(instance, Business):
        language = instance.owner.user.language
    elif hasattr(instance, "language"):
        language = instance.language

    file_path = os.path.join(settings.BASE_DIR, "languages", language + ".json")

    file = open(file_path)
    data = json.load(file)

    return data, language
