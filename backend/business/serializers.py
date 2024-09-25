from business.functions import get_business_rank_value
from business.models import (
    Business,
    BusinessToken,
    BusinessTimetable,
    BusinessHighlight,
)
from insights.models import BusinessLike
from insights.models import BusinessRepost
from moments.models import EventMoment
from posts.models import BusinessPost
from profiles.models import BusinessProfile
from profiles.models import UserProfile
from rest_framework import serializers
from services.date import get_yesterday_and_today
from services.images import crop_image_white_line
from services.utils import update_for_object, pop_or_none
from shared.models import Location
from shared.serializers import (
    CreateLocationSerializer,
    LocationSerializer,
    PhoneSerializer,
    CreateCoordinateSerializer,
    StaticFeatureSerializer,
)


class BusinessTimetableSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessTimetable
        exclude = ("id",)


class CreateBusinessSerializer(serializers.ModelSerializer):
    location = CreateLocationSerializer(required=False)
    timetable = BusinessTimetableSerializer(required=False)

    class Meta:
        model = Business
        exclude = ("owner", "cover_source", "is_approved")

    def validate_location(self, location):
        return Location.objects.create(**location)

    def save(self, source, user):
        categories = pop_or_none("categories", self.validated_data)
        amenities = pop_or_none("amenities", self.validated_data)
        timetable = pop_or_none("timetable", self.validated_data)

        new_source = crop_image_white_line(source)

        timetable = BusinessTimetable.objects.create(**timetable)

        owner, _ = BusinessProfile.objects.get_or_create(user=user)
        owner.accept_terms()

        old_business = Business.objects.filter(owner=owner)

        if old_business.exists():
            return old_business.first()

        business = Business.objects.create(
            owner=owner,
            cover_source=new_source,
            timetable=timetable,
            **self.validated_data,
        )

        if business:
            if categories is not None:
                business.categories.add(*categories)

            if amenities is not None:
                business.amenities.add(*amenities)

            return business

        return None


class UpdateBusinessSerializer(serializers.ModelSerializer):
    location = CreateLocationSerializer(required=False)
    timetable = BusinessTimetableSerializer(required=False)

    class Meta:
        model = Business
        exclude = ("owner", "cover_source", "is_approved")

    def update(self, business, validated_data):
        location = pop_or_none("location", validated_data)
        source = pop_or_none("source", validated_data)
        categories = pop_or_none("categories", validated_data)
        amenities = pop_or_none("amenities", validated_data)
        timetable = pop_or_none("timetable", validated_data)

        if location is not None:
            business.location.update(location)

        if source is not None:
            business.cover_source = crop_image_white_line(source)

        if categories is not None:
            business.categories.clear()
            business.categories.add(*categories)

        if amenities is not None:
            business.amenities.clear()
            business.amenities.add(*amenities)

        if timetable is not None:
            business.timetable.update(timetable)

        update_for_object(business, validated_data)

        business.save()

        return business


class BusinessMeSerializer(serializers.Serializer):
    liked = serializers.SerializerMethodField()

    def __init__(self, instance, **kwargs):
        super().__init__(instance, **kwargs)

        request = self.context.get("req")
        self.request_data = request.data
        self.user = request.user

    def get_liked(self, business):
        likes = BusinessLike.objects.filter(business=business, user=self.user)
        return likes.exists()


SHORT_BUSINESS_SERIALIZER_FIELDS = ("id", "name", "cover_source", "city")


class BusinessIdSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()

    def get_id(self, business):
        return business.uuid


class ShortBusinessSerializer(serializers.ModelSerializer, BusinessIdSerializer):
    city = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = SHORT_BUSINESS_SERIALIZER_FIELDS

    def get_city(self, business):
        if business.location is not None:
            return business.location.city
        return None


class ShortMyBusinessSerializer(ShortBusinessSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta(ShortBusinessSerializer.Meta):
        fields = SHORT_BUSINESS_SERIALIZER_FIELDS + ("auth_token",)

    def get_auth_token(self, business):
        return BusinessToken.objects.get(business=business).key


class CategoriesBusinessSerializer(serializers.Serializer):
    category = StaticFeatureSerializer()
    categories = StaticFeatureSerializer(many=True)


class PreviewBusinessSerializer(BusinessIdSerializer, serializers.ModelSerializer):
    city = serializers.SerializerMethodField()
    timetable = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = ("id", "name", "city", "cover_source", "timetable", "reposts_count")

    def get_city(self, business):
        if business.location is not None:
            return business.location.city
        return None

    def get_timetable(self, business):
        context = self.context

        date = context.get("date")
        closed_too = context.get("closed_too")

        [yesterday, today] = get_yesterday_and_today(date)

        timetable = business.timetable

        if closed_too:
            timetable = BusinessTimetableSerializer(timetable)
            return timetable.data

        yesterday_timetable = getattr(timetable, yesterday)
        today_timetable = getattr(timetable, today)

        return {f"{yesterday}": yesterday_timetable, f"{today}": today_timetable}


class BusinessHighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessHighlight
        fields = ("id", "title", "content")


class BusinessRankingSerializer(serializers.Serializer):
    ranking = serializers.SerializerMethodField()

    def get_ranking(self, business):
        return get_business_rank_value(business)


class BusinessSerializer(
    serializers.ModelSerializer,
    CategoriesBusinessSerializer,
    BusinessIdSerializer,
    BusinessRankingSerializer,
):
    location = LocationSerializer()
    phone = PhoneSerializer()

    amenities = StaticFeatureSerializer(many=True)

    timetable = BusinessTimetableSerializer()

    likes = serializers.SerializerMethodField()
    me = serializers.SerializerMethodField()

    has_posts = serializers.SerializerMethodField()
    reposts_count = serializers.SerializerMethodField()

    highlights = serializers.SerializerMethodField()

    delivery_options = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False
    )

    events = serializers.SerializerMethodField()

    class Meta:
        model = Business
        exclude = (
            "is_approved",
            "settings",
            "owner",
            "created_at",
            "updated_at",
            "extra_data",
        )

    def get_id(self, business):
        return business.uuid

    def get_likes(self, business):
        return business.likes.count()

    def get_me(self, business):
        return BusinessMeSerializer(business, context=self.context).data

    def get_has_posts(self, business):
        count = BusinessPost.objects.filter(business=business).count()
        return count > 0

    def get_reposts_count(self, business):
        return BusinessRepost.objects.get_this_week_count(business)

    def get_highlights(self, business):
        highlights = BusinessHighlight.objects.filter(business=business)
        highlights = BusinessHighlightSerializer(highlights, many=True)

        return highlights.data

    def get_events(self, business):
        from moments.serializers import ShortVenueEventPreviewSerializer

        events = EventMoment.objects.filter(business=business).order_by("date", "time")

        events = ShortVenueEventPreviewSerializer(events, many=True)
        return events.data


class EditBusinessSerializer(
    serializers.ModelSerializer, CategoriesBusinessSerializer, BusinessIdSerializer
):
    amenities = StaticFeatureSerializer(required=False, many=True)
    location = LocationSerializer()
    phone = PhoneSerializer()
    timetable = BusinessTimetableSerializer()

    class Meta:
        model = Business
        exclude = ("owner", "extra_data", "likes")


class MyBusinessSerializer(EditBusinessSerializer, BusinessRankingSerializer):
    auth_token = serializers.SerializerMethodField()
    has_user_profile = serializers.SerializerMethodField()

    def get_auth_token(self, business):
        return BusinessToken.objects.get(business=business).key

    def get_has_user_profile(self, business):
        user = business.owner.user
        profile = UserProfile.objects.filter(user=user)

        return profile.exists()


class ShortBusinessGETParamsSerializer(serializers.Serializer):
    coordinate = CreateCoordinateSerializer()
    place_id = serializers.CharField(required=False)
    offset = serializers.IntegerField()


class BusinessGETParamsSerializer(ShortBusinessGETParamsSerializer):
    categories = serializers.ListField(child=serializers.IntegerField(), required=False)
    amenities = serializers.ListField(child=serializers.IntegerField(), required=False)
    price_target = serializers.IntegerField()
    type = serializers.IntegerField(allow_null=True)
    date = serializers.DateTimeField()
    closed_too = serializers.BooleanField()
