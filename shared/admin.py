from django.contrib import admin
from django.contrib.gis.db import models as geomodels

from shared.models import Location, Amenity, MiddleSource, UserInterest, BusinessCategory
from .widgets import LatLongWidget


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("place_id", "address", "id", "has_coordinate")
    formfield_overrides = {
        geomodels.PointField: {"widget": LatLongWidget},
    }

    @admin.display(
        boolean=True,
        description='has coordinate',
    )
    def has_coordinate(self, location):
        return location.coordinate is not None


@admin.register(BusinessCategory)
class BusinessCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "title")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("id", "title")


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ("id", "title")


admin.site.register(MiddleSource)
