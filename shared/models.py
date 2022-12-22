from django.contrib.gis.db import models as geomodels
from django.db import models
from django.db.models.query_utils import Q


from core.fields import UniqueNameFileField
from core.models import TimestampModel
from image_detector.NSFWDetector import is_moderated_source_valid
from shared.managers import LocationManager

char_options = {"max_length": 128, "blank": True, "null": True}


class Location(TimestampModel):
    address = models.CharField(**char_options)
    city = models.CharField(**char_options)
    coordinate = geomodels.PointField(blank=True, null=True)
    place_id = models.CharField(max_length=256, blank=True, default="")

    objects = LocationManager()

    class Meta:
        indexes = [
            models.Index(
                fields=["place_id"],
                condition=~Q(place_id=None),
                name="%(app_label)s_place_id_part_ix",
            ),
            models.Index(fields=["coordinate"]),
        ]

    def update(self, data):
        coordinate = data.get("coordinate")

        address = data.get("address", None)
        place_id = data.get("place_id")

        self.coordinate = coordinate
        self.address = address
        self.place_id = place_id

        self.save()

    def __str__(self):
        return f"{self.id} • {self.address}"


class Services(models.Model):
    title = models.CharField(max_length=64)

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class BusinessCategory(Services):
    pass


class EventCategory(Services):
    pass


class Amenity(Services):
    pass


class UserInterest(Services):
    pass


def middle_source_url(_, filename):
    return f"utils/middle/{filename}"


class MiddleSource(models.Model):
    source = UniqueNameFileField(max_length=255, upload_to=middle_source_url)

    def is_valid(self):
        is_valid_source = is_moderated_source_valid(self.source)

        self.delete()

        return is_valid_source
