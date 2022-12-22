from django.contrib.gis.geos import Point
from django.db import models

from servicies.geo import get_place_id
from servicies.utils import get_point_coordinate


class LocationManager(models.Manager):

    def _get_coordinate(self, **kwargs):
        coordinate = kwargs.pop("coordinate")
        if not isinstance(coordinate, Point):
            coordinate = get_point_coordinate(coordinate)

        return coordinate

    def create(self, *args, **kwargs):
        coordinate = self._get_coordinate(**kwargs)
        kwargs.pop("coordinate")
        return super().create(coordinate=coordinate, **kwargs)

    def create_with_place_id(self, *args, **kwargs):
        coordinate = self._get_coordinate(**kwargs)

        place_id = get_place_id(coordinate)

        return super().create(coordinate=coordinate, place_id=place_id)
