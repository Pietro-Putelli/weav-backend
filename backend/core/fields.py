import os
from typing import Any
import uuid

import shortuuid
from django.db import models

from core.storage_backends import MediaStorage


class TextField(models.TextField):
    def get_prep_value(self, value):
        if value == "":
            return None
        return value


class UniqueNameFileField(models.FileField):
    def generate_filename(self, instance, filename):
        _, ext = os.path.splitext(filename)
        name = f"{uuid.uuid4().hex}{ext}"
        return super().generate_filename(instance, name)

    def __init__(
        self, verbose_name=None, name=None, upload_to="", storage=None, **kwargs
    ):
        storage = MediaStorage()
        super().__init__(verbose_name, name, upload_to, storage, **kwargs)


def generate_short_uuid():
    return shortuuid.uuid()


class ShortUUIDField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = generate_short_uuid
        kwargs["unique"] = True
        kwargs["max_length"] = 22
        kwargs["editable"] = False

        super().__init__(*args, **kwargs)
