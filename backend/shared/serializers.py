from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from shared.models import Location, BusinessCategory


class CoordinateSerializer(serializers.Serializer):
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    def get_longitude(self, instance):
        return instance.x

    def get_latitude(self, instance):
        return instance.y


class CreateCoordinateSerializer(serializers.Serializer):
    longitude = serializers.FloatField()
    latitude = serializers.FloatField()

    def validate(self, coordinate):
        longitude = coordinate.get("longitude")
        latitude = coordinate.get("latitude")

        if longitude is not None and latitude is not None:
            return Point(longitude, latitude, srid=4326)

        ValidationError("Invalid coordinate")


class CreateLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("coordinate", "city", "place_id", "address")

    def validate_coordinate(self, coordinate):
        if isinstance(coordinate, list):
            longitude = coordinate[0]
            latitude = coordinate[1]
        else:
            longitude = coordinate.get("longitude")
            latitude = coordinate.get("latitude")

        if longitude is not None and latitude is not None:
            return Point(longitude, latitude)

        ValidationError("Invalid coordinate")


class LocationSerializer(serializers.ModelSerializer):
    coordinate = CoordinateSerializer()

    class Meta:
        model = Location
        fields = ("coordinate", "city", "place_id", "address")


class PhoneSerializer(serializers.Serializer):
    code = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()

    def get_code(self, instance):
        if not hasattr(instance, "country_code"):
            return None
        return "+" + str(instance.country_code)

    def get_number(self, instance):
        if not hasattr(instance, "national_number"):
            return None
        return str(instance.national_number)


class CreatePhoneSerializer(serializers.Serializer):
    code = serializers.CharField(allow_blank=True)
    number = serializers.CharField(allow_blank=True)

    def validate(self, instance):
        code = instance.get("code")
        number = instance.get("number")

        return f"{code}{number}"


class StaticFeatureSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    def get_id(self, feature):
        if isinstance(feature, BusinessCategory):
            return f"category_{feature.id}"
        return f"amenity_{feature.id}"

    def get_title(self, feature):
        request = self.context.get("req")

        if request is not None:
            language = request.user.language
        else:
            language = self.context.get("language", "en")

        return getattr(feature, language)

    def get_icon(self, feature):
        icon_name = feature.en.replace(" ", ".").lower()
        return icon_name
