from rest_framework import serializers
from chances.models import UserChance, EventChance
from profiles.serializers import ShortUserProfileSerializer
from moments.serializers import VeryShortEventMomentSerializer


class ChanceSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()

    def get_user(self, chance):
        user = self.context.get("user")

        if user == chance.first:
            user = chance.second
        else:
            user = chance.first

        return ShortUserProfileSerializer(user).data


class UserChanceSerializer(serializers.ModelSerializer, ChanceSerializer):
    class Meta:
        model = UserChance
        fields = ("id", "user")


class EventChanceSerializer(serializers.ModelSerializer, ChanceSerializer):
    event = VeryShortEventMomentSerializer()

    class Meta:
        model = EventChance
        fields = ("id", "user", "event")
