from datetime import timedelta, datetime

from django.utils import timezone
from rest_framework import serializers
from rest_framework.serializers import ValidationError

from business.models import Business
from business.serializers import ShortBusinessSerializer, ShortChatBusinessSerializer
from image_detector.NSFWDetector import is_moderated_source_valid
from insights.choices import RepostAndShareChoices
from insights.models import BusinessRepost
from insights.utils import add_repost_to_event, add_repost_to_business
from moments.models import EventMomentSlice, UserMoment, EventMoment
from moments.tag_serializers import UrlTagSerializer, LocationTagSerializer
from moments.utils import get_event_participants
from profiles.serializers import ShortUserProfileSerializer, ShortUserProfileChatSerializer
from servicies.date import get_date_tz_aware
from servicies.utils import pop_or_none, update_for_object
from shared.models import Location
from shared.serializers import CreateLocationSerializer, LocationSerializer, PhoneSerializer
from users.models import User


class CreateTagSerializer(serializers.Serializer):
    business_tag = serializers.IntegerField(required=False)
    users_tag = serializers.ListField(required=False, child=serializers.CharField())
    location_tag = CreateLocationSerializer(required=False)

    def validate_business_tag(self, business_id):
        if business_id is not None:
            try:
                business = Business.objects.get(id=business_id)
                return business
            except Business.DoesNotExist:
                pass
        return None

    def validate_location_tag(self, location):
        if location is not None:
            return Location.objects.create(**location)
        return None

    def validate_users_tag(self, value):
        if value is not None or len(value) > 0:
            return value
        return None


class CreateUserMomentSerializer(serializers.ModelSerializer, CreateTagSerializer):
    # Location of the moment
    location = CreateLocationSerializer()
    slice_id = serializers.IntegerField(required=False)
    duration = serializers.FloatField()

    class Meta:
        model = UserMoment
        exclude = ("user",)

    def save(self, user, source):
        location_data = self.validated_data.pop("location")
        location = Location.objects.create_with_place_id(**location_data)

        users_tag = pop_or_none("users_tag", self.validated_data)
        business_tag = pop_or_none("business_tag", self.validated_data)
        location_tag = pop_or_none("location_tag", self.validated_data)

        duration = pop_or_none("duration", self.validated_data)
        end_at = timezone.now() + timedelta(minutes=duration)

        slice = None
        # Means that the user is reposting an event moment
        if "slice_id" in self.validated_data:
            slice_id = self.validated_data.pop("slice_id")
            slice = EventMomentSlice.objects.get(id=slice_id)

            add_repost_to_event(user, slice.moment)

        if business_tag is not None:
            add_repost_to_business(user, business_tag)

        moment = UserMoment.objects.create(user=user, location=location, business_tag=business_tag,
                                           source=source, event_moment=slice,
                                           location_tag=location_tag, end_at=end_at,
                                           **self.validated_data)

        if source is not None:
            is_valid_source = is_moderated_source_valid(moment.source)

            if not is_valid_source:
                moment.delete()
                return None

        if users_tag is not None:
            users = User.objects.filter(username__in=users_tag)

            for user in users:
                moment.users_tag.add(user)

        return moment


class MomentTagsSerializer(serializers.Serializer):
    users_tag = serializers.SerializerMethodField()
    url_tag = serializers.SerializerMethodField()
    business_tag = ShortBusinessSerializer()
    location_tag = LocationTagSerializer()

    def get_url_tag(self, instance):
        url_tag = instance.url_tag

        if url_tag != "" and url_tag is not None:
            return UrlTagSerializer(url_tag).data
        return None

    def get_users_tag(self, instance):
        users = instance.users_tag.all()

        if users.count() > 0:
            return ShortUserProfileSerializer(users, many=True).data
        return None


class EventMomentSliceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMomentSlice
        exclude = ("moment",)


# Use this in case you get only one slice, so you can know the business.
class ShortEventMomentSliceSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    class Meta:
        model = EventMomentSlice
        fields = ("id", "title", "source")

    def get_id(self, slice):
        return slice.moment.id

    def get_title(self, slice):
        return slice.moment.title


class UserMomentSerializer(serializers.ModelSerializer, MomentTagsSerializer):
    id = serializers.SerializerMethodField()
    user = ShortUserProfileChatSerializer()
    event_moment = ShortEventMomentSliceSerializer()
    has_custom_source = serializers.SerializerMethodField()

    class Meta:
        model = UserMoment
        fields = "__all__"

    def get_id(self, moment):
        return f"moment.user.{moment.id}"

    def get_has_custom_source(self, moment):
        return hasattr(moment, "business_tag") and bool(moment.source)


class EventParticipantSerializer(serializers.Serializer):
    users = ShortUserProfileSerializer(many=True)
    count = serializers.IntegerField()


class EventMomentSlicesSerializer(serializers.Serializer):
    slices = serializers.SerializerMethodField()

    def get_slices(self, moment):
        slices = EventMomentSlice.objects.filter(moment=moment).order_by("created_at")
        slices = EventMomentSliceSerializer(slices, many=True)
        return slices.data


class VeryShortEventMomentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMoment
        fields = ("id", "title")


class ShortEventMomentSerializer(EventMomentSlicesSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    business = ShortBusinessSerializer()


class EventMomentDetailSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    is_going = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()
    business = ShortChatBusinessSerializer()

    class Meta:
        model = EventMoment
        fields = (
            "business", "date", "time", "participants", "guests", "price", "instagram", "website",
            "ticket", "description", "location", "is_going", "participants_count")

    def get_location(self, event):
        location = event.business.location

        if event.location is not None:
            location = event.location

        return LocationSerializer(location).data

    def get_participants(self, event):
        user = self.context.get("user")

        participants = get_event_participants(event.id, user, 0, 4)
        return participants

    def get_is_going(self, event):
        user = self.context.get("user")
        return user in event.participants.all()

    def get_participants_count(self, event):
        return event.participants.count()


class EventMomentSerializer(ShortEventMomentSerializer):
    location = LocationSerializer()
    selected_slice = serializers.SerializerMethodField()

    class Meta:
        model = EventMoment
        fields = "__all__"

    def get_selected_slice(self, _):
        selected_id = self.context.get("selected")
        selected = f"slice.{selected_id}"
        return selected


class MyEventMomentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMoment
        fields = ("id", "title", "date", "time")


class CurrentEventMomentSerializer(serializers.ModelSerializer, EventMomentSlicesSerializer):
    location = LocationSerializer()

    class Meta:
        model = EventMoment
        exclude = ("business", "participants")


class CreateEventMomentSerializer(serializers.Serializer):
    date = serializers.CharField()
    time = serializers.CharField()
    title = serializers.CharField()
    location = CreateLocationSerializer(required=False)

    class Meta:
        model = EventMoment
        exclude = ("business",)

    def validate_location(self, location):
        if location is None:
            return None
        return Location.objects.create(**location)

    def validate_date(self, date):
        try:
            new_date = datetime.strptime(date, "%Y-%m-%d")
            date = get_date_tz_aware(new_date)
            return date
        except ValueError as error:
            raise ValidationError(error)

    def validate_time(self, time):
        try:
            return datetime.strptime(time, "%H:%M").time()
        except ValueError:
            raise ValidationError("Invalid time")

    def validate_title(self, title):
        if len(title) < 8:
            raise ValidationError("Title must be at least 4 characters long")
        return title


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
