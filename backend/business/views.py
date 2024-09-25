import json

import pydash
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from authentication.api_views import (
    BusinessAuthenticationAPIView,
    AuthenticationMixinAPIView,
)
from authentication.decorators import authentication_mixin
from authentication.decorators import business_authentication
from business.functions import (
    get_businesses_nearby,
    get_nearest_businesses,
    get_businesses_for_spot,
)
from business.models import Business
from business.serializers import (
    BusinessSerializer,
    ShortBusinessSerializer,
    BusinessGETParamsSerializer,
    EditBusinessSerializer,
    CreateBusinessSerializer,
    MyBusinessSerializer,
    ShortMyBusinessSerializer,
    UpdateBusinessSerializer,
    PreviewBusinessSerializer,
    ShortBusinessGETParamsSerializer,
)
from core.querylimits import QueryLimits
from devices.models import Device
from insights.utils import (
    add_business_profile_visits,
    add_business_like,
    remove_business_like,
)
from shared.models import BusinessCategory, Amenity
from shared.serializers import CreateCoordinateSerializer, StaticFeatureSerializer


def get_business_data(request):
    form_data = request.data

    source = form_data.get("cover_source")
    json_data = form_data.get("data")
    data = json.loads(json_data)

    extra_data = data.get("extra_data")

    return source, data, extra_data


@api_view(["POST"])
def create_business(request):
    source, data, extra_data = get_business_data(request)

    serializer = CreateBusinessSerializer(data=data)

    if serializer.is_valid():
        business = serializer.save(
            source=source, user=request.user, extra_data=extra_data
        )
        business = MyBusinessSerializer(business)

        return Response(business.data, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_400_BAD_REQUEST)


class BusinessAPIView(BusinessAuthenticationAPIView):
    def put(self, request):
        source, data, extra_data = get_business_data(request)

        serializer = UpdateBusinessSerializer(request.business, data=data)

        if serializer.is_valid():
            business = serializer.save(source=source)

            language = business.owner.user.language

            business = EditBusinessSerializer(business, context={"language": language})
            return Response(business.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        business = request.business
        Business.objects.filter(id=business.id).delete()

        # Setup device logged as user
        Device.objects.filter(user=business.owner.user).update(is_business=False)

        return Response(status=HTTP_200_OK)


@api_view(["POST"])
def get_businesses(request):
    serializer = BusinessGETParamsSerializer(data=request.data)

    if serializer.is_valid():
        data = serializer.validated_data
        businesses = get_businesses_nearby(data)

        context = pydash.pick(data, ["date", "closed_too"])

        response = PreviewBusinessSerializer(businesses, many=True, context=context)

        return Response(response.data, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_400_BAD_REQUEST)


# Need to use POST method because of COORDINATE to get user's distance from BUSINESS.
@api_view(["POST"])
def get_business_by_id(request):
    uuid = (request.data or request.query_params).get("id")

    try:
        business = Business.objects.get(uuid=uuid)
    except Business.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    add_business_profile_visits(request.user, business)

    business = BusinessSerializer(business, context={"req": request})
    return Response(business.data, status=HTTP_200_OK)


@api_view(["POST"])
def search_business(request):
    data = request.data

    value = data.get("value")
    offset = data.get("offset")
    serializer = CreateCoordinateSerializer(data=data.get("coordinate"))

    up_offset = offset + QueryLimits.SEARCH_BUSINESS_LIMIT

    if value == "" and serializer.is_valid():
        user_position = serializer.validated_data
        businesses = get_nearest_businesses(user_position, offset)
    else:
        businesses = Business.objects.only_approved().filter(name__icontains=value)[
            offset:up_offset
        ]

    businesses = ShortBusinessSerializer(businesses, many=True)

    return Response(businesses.data, status=HTTP_200_OK)


@api_view(["POST"])
def get_ranked_businesses(request):
    data = request.data

    place_id = data.get("place_id")
    category = data.get("category")

    venues = Business.objects.get_business_rank(place_id, category)
    venues = BusinessSerializer(venues, many=True, context={"req": request})

    return Response(venues.data, status=HTTP_200_OK)


@api_view(["GET"])
@authentication_mixin
def get_my_business_data(request):
    user = request.user

    business_id = request.query_params.get("businessId", None)

    if business_id is not None:
        business = Business.objects.filter(uuid=business_id).first()
        business = MyBusinessSerializer(business)

        response = business.data

    else:
        businesses = Business.objects.filter(owner__user=user)

        if businesses.count() == 0:
            return Response(status=HTTP_404_NOT_FOUND)

        businesses = MyBusinessSerializer(businesses, many=True)
        response = businesses.data

    device = Device.objects.filter(user=user).first()

    if device is not None and not device.is_business:
        device.update_is_business(True)

    return Response(response, status=HTTP_200_OK)


class BusinessLikeAPIView(APIView):
    def put(self, request):
        data = request.data
        business_id = data.get("id")

        try:
            business = Business.objects.get(uuid=business_id)
            likes = business.likes

            profile = request.user.profile

            params = (request.user, business)

            if profile in likes.all():
                likes.remove(profile)
                remove_business_like(*params)
            else:
                likes.add(profile)
                add_business_like(*params)

            return Response(status=HTTP_200_OK)

        except Business.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    # Use POST because need user position
    def post(self, request):
        profile = request.user.profile

        venues = []
        queryset = Business.objects.all()

        for venue in queryset:
            if profile in venue.likes.all():
                venues.append(venue)

        businesses = BusinessSerializer(venues, many=True, context={"req": request})
        return Response(businesses.data, status=HTTP_200_OK)


@api_view(["POST"])
def get_businesses_spot(request):
    data = request.data

    serializer = ShortBusinessGETParamsSerializer(data=data)

    if serializer.is_valid():
        data = serializer.validated_data

        businesses = get_businesses_for_spot(data)
        businesses = ShortBusinessSerializer(businesses, many=True)

        return Response(businesses.data, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@business_authentication
def update_business_profile_settings(request):
    settings = request.data.get("settings")
    allow_chat = settings.get("allow_chat")

    business = request.business

    if allow_chat is not None:
        business.allow_chat = allow_chat
        business.save()
    else:
        business.update_settings(settings)

    return Response(status=HTTP_200_OK)


class BusinessFeaturesAPIView(AuthenticationMixinAPIView):
    def get(self, request, endpoint):
        categories = []
        amenities = []

        language = request.user.language
        context = {"language": language}

        kwargs = {"context": context, "many": True}

        if endpoint == "both":
            categories = BusinessCategory.objects.all().order_by("-weight")
            categories = StaticFeatureSerializer(categories, **kwargs).data

            amenities = Amenity.objects.all().order_by("-weight")
            amenities = StaticFeatureSerializer(amenities, **kwargs).data

        if endpoint == "categories":
            categories = BusinessCategory.objects.all().order_by("-weight")
            categories = StaticFeatureSerializer(categories, **kwargs).data

        if endpoint == "amenities":
            amenities = Amenity.objects.all().order_by("-weight")
            amenities = StaticFeatureSerializer(amenities, **kwargs).data

        return Response(
            {"amenities": amenities, "categories": categories}, status=HTTP_200_OK
        )
