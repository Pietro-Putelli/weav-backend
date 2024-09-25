from rest_framework import serializers

from shared.serializers import CoordinateSerializer


class UrlTagSerializer(serializers.Serializer):
    type = serializers.CharField(default="url_tag")
    value = serializers.SerializerMethodField()

    def get_value(self, instance):
        return instance


class LocationTagSerializer(serializers.Serializer):
    type = serializers.CharField(default="location_tag")
    coordinate = CoordinateSerializer()
    value = serializers.SerializerMethodField()

    def get_value(self, instance):
        return instance.address
