from django.contrib.gis.geos import Point
from django.db import models

from services.utils import get_point_coordinate, pop_or_none


class LocationManager(models.Manager):
    def _get_coordinate(self, **kwargs):
        coordinate = pop_or_none("coordinate", kwargs)

        if not coordinate:
            return None

        if not isinstance(coordinate, Point):
            coordinate = get_point_coordinate(coordinate)

        return coordinate

    def create(self, *_, **kwargs):
        coordinate = pop_or_none("coordinate", kwargs)

        if coordinate is not None:
            if not isinstance(coordinate, Point):
                coordinate = get_point_coordinate(coordinate)

        return super().create(coordinate=coordinate, **kwargs)
