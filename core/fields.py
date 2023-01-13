import os
import uuid

import shortuuid
from django.db import models


class TextField(models.TextField):
    def get_prep_value(self, value):
        if value == '':
            return None
        return value


class UniqueNameFileField(models.FileField):
    def generate_filename(self, instance, filename):
        _, ext = os.path.splitext(filename)
        name = f'{uuid.uuid4().hex}{ext}'
        return super().generate_filename(instance, name)


def generate_short_uuid():
    return shortuuid.uuid()


class ShortUUIDField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['default'] = generate_short_uuid
        kwargs['unique'] = True
        kwargs['max_length'] = 22
        kwargs['editable'] = False

        super().__init__(*args, **kwargs)
