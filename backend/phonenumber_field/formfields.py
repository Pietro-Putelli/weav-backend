from django.conf import settings
from django.core import validators
from django.forms.fields import CharField

from phonenumber_field.phonenumber import to_python, validate_region
from phonenumber_field.widgets import RegionalPhoneNumberWidget


class PhoneNumberField(CharField):
    widget = RegionalPhoneNumberWidget

    def __init__(self, *args, region=None, widget=None, **kwargs):
        validate_region(region)
        self.region = region or getattr(settings, "PHONENUMBER_DEFAULT_REGION", None)

        if widget is None:
            try:
                widget = self.widget(region=self.region)
            except TypeError:
                widget = self.widget()

        super().__init__(*args, widget=widget, **kwargs)
        self.widget.input_type = "tel"

    def to_python(self, value):
        phone_number = to_python(value, region=self.region)

        if phone_number in validators.EMPTY_VALUES:
            return self.empty_value

        return phone_number
