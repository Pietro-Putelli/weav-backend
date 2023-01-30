from rest_framework import serializers

from business.functions import get_business_rank_value
from business.models import Business, BusinessToken
from insights.models import BusinessLike
from posts.models import BusinessPost
from servicies.images import crop_image_white_line
from servicies.utils import update_for_object, pop_or_none
from shared.models import Location
from shared.serializers import (CreateLocationSerializer,
                                LocationSerializer,
                                PhoneSerializer, CreateCoordinateSerializer,
                                StaticFeatureSerializer)


class CreateBusinessSerializer(serializers.ModelSerializer):
    location = CreateLocationSerializer(required=False)

    class Meta:
        model = Business
        exclude = ("owner", "cover_source", "is_approved")

    def validate_location(self, location):
        return Location.objects.create(**location)

    def save(self, source, user, **kwargs):
        categories = pop_or_none("categories", self.validated_data)
        amenities = pop_or_none("amenities", self.validated_data)

        new_source = crop_image_white_line(source)

        business = Business.objects.create(
            owner=user,
            cover_source=new_source,
            **self.validated_data
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

    class Meta:
        model = Business
        exclude = ("owner", "cover_source", "is_approved")

    def update(self, business, validated_data):
        location = pop_or_none("location", validated_data)
        source = pop_or_none("source", validated_data)
        categories = pop_or_none("categories", validated_data)
        amenities = pop_or_none("amenities", validated_data)

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
        return BusinessLike.objects.filter(business=business, user=self.user).exists()


SHORT_BUSINESS_SERIALIZER_FIELDS = ("id", "name", "cover_source", "city", "type")


class BusinessIdSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()

    def get_id(self, business):
        return business.uuid


class ShortBusinessSerializer(serializers.ModelSerializer, BusinessIdSerializer):
    city = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = SHORT_BUSINESS_SERIALIZER_FIELDS

    def get_city(self, business):
        if business.location is not None:
            return business.location.city
        return None

    def get_type(self, business):
        if business.location is not None:
            return "venue"
        return "event"


class ShortChatBusinessSerializer(ShortBusinessSerializer):
    public_key = serializers.CharField()

    class Meta(ShortBusinessSerializer.Meta):
        fields = SHORT_BUSINESS_SERIALIZER_FIELDS + ("public_key",)


class ShortMyBusinessSerializer(ShortBusinessSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta(ShortBusinessSerializer.Meta):
        fields = SHORT_BUSINESS_SERIALIZER_FIELDS + ("auth_token",)

    def get_auth_token(self, business):
        return BusinessToken.objects.get(business=business).key


class BusinessSerializer(serializers.ModelSerializer, BusinessIdSerializer):
    location = LocationSerializer()
    phone = PhoneSerializer()

    categories = StaticFeatureSerializer(many=True)
    amenities = StaticFeatureSerializer(many=True)

    likes = serializers.SerializerMethodField()
    ranking = serializers.SerializerMethodField()
    me = serializers.SerializerMethodField()

    has_posts = serializers.SerializerMethodField()
    has_moment = serializers.SerializerMethodField()

    class Meta:
        model = Business
        exclude = ("is_approved", "settings", "owner")

    def get_id(self, business):
        return business.uuid

    def get_likes(self, business):
        return business.likes.count()

    def get_ranking(self, business):
        return get_business_rank_value(business)

    def get_me(self, business):
        return BusinessMeSerializer(business, context=self.context).data

    def get_has_posts(self, business):
        count = BusinessPost.objects.filter(business=business).count()
        return count > 0

    def get_has_moment(self, business):
        from moments.models import EventMoment

        count = EventMoment.objects.filter(business=business).count()
        return count > 0


class CategoriesBusinessSerializer(serializers.Serializer):
    categories = serializers.SerializerMethodField()

    def get_categories(self, business):
        category = business.category

        if category is None:
            return None

        subcategories = business.categories.all()
        categories = list(subcategories)
        categories.insert(0, category)

        serialized = StaticFeatureSerializer(categories, many=True)
        return serialized.data


class EditBusinessSerializer(serializers.ModelSerializer, CategoriesBusinessSerializer,
                             BusinessIdSerializer):
    category = StaticFeatureSerializer()
    amenities = StaticFeatureSerializer(required=False, many=True)
    location = LocationSerializer()
    phone = PhoneSerializer()

    class Meta:
        model = Business
        exclude = ("owner", "settings", "extra_data", "likes")


class MyBusinessSerializer(EditBusinessSerializer):
    auth_token = serializers.SerializerMethodField()

    def get_auth_token(self, business):
        return BusinessToken.objects.get(business=business).key


class BusinessGETParamsSerializer(serializers.Serializer):
    coordinate = CreateCoordinateSerializer()
    categories = serializers.ListField(child=serializers.IntegerField())
    amenities = serializers.ListField(child=serializers.IntegerField())
    price_target = serializers.IntegerField()
    is_city = serializers.BooleanField()
    place_id = serializers.CharField()
    offset = serializers.IntegerField()
