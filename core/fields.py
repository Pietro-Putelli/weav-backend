import os
import uuid
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
