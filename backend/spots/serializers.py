from rest_framework import serializers

from business.models import Business
from profiles.serializers import ShortUserProfileSerializer
from .models import Spot


class SpotIdSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()

    def get_id(self, spot):
        return spot.uuid


class SpotSerializer(SpotIdSerializer, serializers.ModelSerializer):
    profile = ShortUserProfileSerializer()
    is_replied = serializers.SerializerMethodField()
    business_id = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()

    class Meta:
        model = Spot
        fields = [
            "id",
            "profile",
            "content",
            "business_id",
            "is_replied",
            "is_anonymous",
            "created_at",
            "replies_count",
        ]

    def get_is_replied(self, spot):
        profile = self.context.get("user").profile

        return profile in spot.replies.all()

    def get_business_id(self, spot):
        return spot.business.uuid

    def get_replies_count(self, spot):
        return spot.replies.count()


class CreateSpotSerializer(SpotIdSerializer):
    content = serializers.CharField(max_length=300)
    business_id = serializers.CharField(max_length=22)
    is_anonymous = serializers.BooleanField(default=False)

    def save(self, profile):
        business_id = self.validated_data.pop("business_id")

        try:
            business = Business.objects.get(uuid=business_id)
        except Business.DoesNotExist:
            raise serializers.ValidationError("Business does not exist")

        spot = Spot.objects.create(
            profile=profile, business=business, **self.validated_data
        )

        return spot
