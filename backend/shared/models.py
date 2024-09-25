from django.contrib.gis.db import models as geomodels
from django.db import models
from django.db.models.query_utils import Q
from core.fields import UniqueNameFileField
from core.models import TimestampModel
from shared.managers import LocationManager

char_options = {"max_length": 128, "blank": True, "null": True}

allow_blank = {"blank": True, "null": True}


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
    en = models.CharField(max_length=64, **allow_blank)
    it = models.CharField(max_length=64, **allow_blank)
    weight = models.IntegerField(default=1, **allow_blank)

    def __str__(self):
        return self.en

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
