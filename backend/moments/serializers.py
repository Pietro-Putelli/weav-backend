from datetime import timedelta
from shared.serializers import CreateCoordinateSerializer

from business.models import Business
from business.serializers import ShortBusinessSerializer
from django.utils import timezone
from insights.utils import add_repost_to_business, add_repost_to_event
from moments.models import EventMoment, UserMoment
from moments.tag_serializers import LocationTagSerializer, UrlTagSerializer
from moments.utils import get_event_participants
from profiles.models import UserProfile
from profiles.serializers import (
    ShortUserProfileSerializer,
    ShortUserProfileSerializer,
    VeryShortUserProfileSerializer,
)
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from services.utils import pop_or_none, update_for_object
from shared.models import Location
from shared.serializers import CreateLocationSerializer, LocationSerializer
from users.models import User


class MomentIdSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()

    def get_id(self, moment):
        return moment.uuid


class CreateTagSerializer(serializers.Serializer):
    business_tag = serializers.CharField(required=False)
    participants = serializers.ListField(required=False, child=serializers.CharField())
    location_tag = CreateLocationSerializer(required=False)

    def validate_business_tag(self, uuid):
        if uuid is not None:
            try:
                business = Business.objects.get(uuid=uuid)
                return business
            except Business.DoesNotExist:
                pass
        return None

    def validate_location_tag(self, location):
        if location is not None:
            return Location.objects.create(**location)
        return None

    def validate_participants(self, participants):
        if participants is not None or len(participants) > 0:
            return participants
        return None


class CreateUserMomentSerializer(
    serializers.ModelSerializer, CreateTagSerializer, MomentIdSerializer
):
    # Location of the moment
    location = CreateLocationSerializer()
    eventId = serializers.CharField(required=False)
    duration = serializers.FloatField()

    class Meta:
        model = UserMoment
        exclude = ("user",)

    def save(self, profile, source):
        location_data = self.validated_data.pop("location")
        location = Location.objects.create(**location_data)

        participants = pop_or_none("participants", self.validated_data)
        business_tag = pop_or_none("business_tag", self.validated_data)
        location_tag = pop_or_none("location_tag", self.validated_data)

        duration = pop_or_none("duration", self.validated_data)
        end_at = timezone.now() + timedelta(minutes=duration)

        event = None
        # Means that the user is reposting an event moment
        if "eventId" in self.validated_data:
            eventId = self.validated_data.pop("eventId")
            event = EventMoment.objects.get(uuid=eventId)

            add_repost_to_event(profile.user, event)

        if business_tag is not None:
            add_repost_to_business(profile.user, business_tag)

        moment = UserMoment.objects.create(
            user=profile,
            location=location,
            business_tag=business_tag,
            event=event,
            location_tag=location_tag,
            end_at=end_at,
            source=source,
            **self.validated_data,
        )

        if event is not None:
            moment.ratio = event.ratio
            moment.save()

        if participants is not None:
            users = UserProfile.objects.filter(user__uuid__in=participants)

            for user in users:
                moment.participants.add(user)

        return moment


class MomentTagsSerializer(serializers.Serializer):
    participants = serializers.SerializerMethodField()
    url_tag = serializers.SerializerMethodField()
    business_tag = ShortBusinessSerializer()
    location_tag = LocationTagSerializer()

    def get_url_tag(self, moment):
        url_tag = moment.url_tag

        if url_tag != "" and url_tag is not None:
            return UrlTagSerializer(url_tag).data
        return None

    def get_participants(self, moment):
        users = moment.participants.all()

        if users.count() > 0:
            return ShortUserProfileSerializer(users, many=True).data
        return None


class ShortEventSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = EventMoment
        fields = ("id", "title", "cover")

    def get_id(self, event):
        return event.uuid


class ShortVenueEventPreviewSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    cover = serializers.FileField()

    class Meta:
        model = EventMoment
        fields = ("id", "ratio", "cover", "date", "time", "periodic_day", "title")

    def get_id(self, event):
        return event.uuid


class UserMomentSerializer(
    serializers.ModelSerializer, MomentTagsSerializer, MomentIdSerializer
):
    user = ShortUserProfileSerializer()
    event = ShortEventSerializer()
    replied = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    has_custom_source = serializers.SerializerMethodField()

    class Meta:
        model = UserMoment
        exclude = ("uuid", "location")

    def get_has_custom_source(self, moment):
        return hasattr(moment, "business_tag") and bool(moment.source)

    def _get_profile(self):
        user = self.context.get("user")

        if user is None:
            return None

        return user if isinstance(user, UserProfile) else user.profile

    def get_replied(self, moment):
        profile = self._get_profile()

        if not profile:
            return None

        return profile in moment.replied_by.all()

    def get_participants(self, moment):
        user = self.context.get("user")

        if user is None:
            return None

        users = moment.participants.all()

        count = users.count()

        if count == 1:
            user = ShortUserProfileSerializer(users, many=True)
            response = user.data
        else:
            users = VeryShortUserProfileSerializer(users[:3], many=True)
            response = users.data

        return {"users": response, "count": count}


class EventParticipantSerializer(serializers.Serializer):
    users = ShortUserProfileSerializer(many=True)
    count = serializers.IntegerField()


class EventGoingSerializer(serializers.Serializer):
    is_going = serializers.SerializerMethodField()

    def get_is_going(self, event):
        user = self.context.get("user")

        profile = user

        if isinstance(user, User):
            profile = user.profile

        return profile in event.participants.all()


class ShortMyEventMomentSerializer(MomentIdSerializer):
    cover = serializers.FileField()
    title = serializers.CharField()
    date = serializers.CharField()
    time = serializers.CharField()
    periodic_day = serializers.CharField()
    has_activity = serializers.BooleanField()
    ratio = serializers.FloatField()
    # distance = serializers.SerializerMethodField(required=False)

    # def get_distance(self, event):
    #     if hasattr(event, "distance"):
    #         return event.distance.m
    #     return None


class ShortEventMomentSerializer(ShortMyEventMomentSerializer, EventGoingSerializer):
    reposts_count = serializers.IntegerField()
    participants = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()

    def get_participants(self, event):
        user = self.context.get("user", None)

        profile = user

        if isinstance(user, User):
            profile = user.profile

        if user is not None:
            participants = get_event_participants(event.uuid, profile, 0, 3)
            return participants

        return None

    def get_business_name(self, event):
        return event.business.name


class EventMomentDetailSerializer(
    ShortEventMomentSerializer, serializers.ModelSerializer, EventGoingSerializer
):
    business = ShortBusinessSerializer()
    location = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    is_going = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = EventMoment
        fields = (
            "cover",
            "ratio",
            "title",
            "business",
            "date",
            "time",
            "participants",
            "guests",
            "price",
            "instagram",
            "website",
            "ticket",
            "description",
            "location",
            "is_going",
            "participants_count",
            "id",
            "end_time",
            "periodic_day",
        )

    def get_location(self, event):
        location = event.business.location

        if event.location is not None:
            location = event.location

        return LocationSerializer(location).data

    def get_participants(self, event):
        user = self.context.get("user")

        profile = user

        if isinstance(user, User):
            profile = user.profile

        participants = get_event_participants(event.uuid, profile, 0, 4)
        return participants

    def get_participants_count(self, event):
        return event.participants.count()


class BusinessEventSerializer(ShortEventMomentSerializer, serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = EventMoment
        fields = (
            "cover",
            "ratio",
            "title",
            "date",
            "time",
            "guests",
            "price",
            "instagram",
            "website",
            "ticket",
            "description",
            "location",
            "id",
            "end_time",
            "periodic_day",
        )

    def get_location(self, event):
        location = event.business.location

        if event.location is not None:
            location = event.location


class EventMomentSerializer(ShortEventMomentSerializer):
    location = LocationSerializer()

    class Meta:
        model = EventMoment
        fields = "__all__"


class CreateOrUpdateEventSerializer(serializers.ModelSerializer):
    title = serializers.CharField()
    location = CreateLocationSerializer(required=False)

    class Meta:
        model = EventMoment
        exclude = ("business", "cover")

    def validate_location(self, location):
        if location is None:
            return None
        return Location.objects.create(**location)

    def validate_title(self, title):
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters long")
        return title

    def save(self, business, cover):
        event = EventMoment.objects.create(
            business=business, cover=cover, **self.validated_data
        )
        return event

    def update(self, event_id, cover):
        try:
            event = EventMoment.objects.get(uuid=event_id)

            if cover is not None:
                event.cover = cover

            update_for_object(event, self.validated_data)

            event.save()
            return event

        except EventMoment.DoesNotExist:
            raise ValidationError("Event does not exist")


class UpdateEventMomentSerializer(serializers.ModelSerializer):
    location = CreateLocationSerializer(required=False)

    class Meta:
        model = EventMoment
        exclude = ("business",)

    def update(self, moment, validated_data):
        location = pop_or_none("location", validated_data)

        if location is not None:
            if moment.location is None:
                moment.location = Location.objects.create(**location)
            else:
                moment.location.update(location)

        update_for_object(moment, validated_data)
        moment.save()

        return moment


class EventRequestSerializer(serializers.Serializer):
    coordinate = CreateCoordinateSerializer()
    place_id = serializers.CharField(required=False)
    offset = serializers.IntegerField()
