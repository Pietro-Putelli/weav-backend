import json

from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from business.authentication import business_authentication, BusinessAuthenticationAPIView
from business.functions import get_businesses_nearby, get_nearest_businesses
from business.models import Business
from business.serializers import BusinessSerializer, ShortBusinessSerializer, \
    BusinessGETParamsSerializer, EditBusinessSerializer, \
    CreateBusinessSerializer, MyBusinessSerializer, ShortMyBusinessSerializer, \
    UpdateBusinessSerializer
from insights.utils import add_business_profile_visits, add_business_like, remove_business_like
from moments.models import EventMoment
from moments.serializers import ShortEventMomentSerializer
from servicies.querylimits import SEARCH_BUSINESS_LIMIT
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
        business = serializer.save(source=source, user=request.user, extra_data=extra_data)
        business = MyBusinessSerializer(business)

        return Response(business.data, status=HTTP_200_OK)

    return Response(status=HTTP_400_BAD_REQUEST)


class BusinessAPIView(BusinessAuthenticationAPIView):
    def put(self, request):
        source, data, extra_data = get_business_data(request)

        serializer = UpdateBusinessSerializer(request.business, data=data)

        if serializer.is_valid():
            business = serializer.save(source=source)
            business = EditBusinessSerializer(business)
            return Response(business.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    def delete(self, request):
        Business.objects.filter(id=request.business.id).delete()
        return Response(status=HTTP_200_OK)


@api_view(["POST"])
def get_businesses(request):
    serializer = BusinessGETParamsSerializer(data=request.data)

    if serializer.is_valid():
        data = serializer.validated_data
        businesses = get_businesses_nearby(data)
        businesses = BusinessSerializer(businesses, many=True, context={"req": request})

        return Response(businesses.data, status=HTTP_200_OK)

    return Response(status=HTTP_400_BAD_REQUEST)


# Need to use POST method because of COORDINATE to get user's distance from BUSINESS.
@api_view(["POST", "GET"])
def get_business_by_id(request):
    business_id = (request.data or request.query_params).get("business_id")

    try:
        business = Business.objects.get(id=business_id)
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

    up_offset = offset + SEARCH_BUSINESS_LIMIT

    if value == "" and serializer.is_valid():
        user_position = serializer.validated_data
        businesses = get_nearest_businesses(user_position, offset)
    else:
        businesses = Business.objects.filter(name__icontains=value)[
                     offset:up_offset]

    businesses = ShortBusinessSerializer(businesses, many=True)

    return Response(businesses.data, status=HTTP_200_OK)


@api_view(["POST"])
def get_ranked_businesses(request):
    data = request.data

    place_id = data.get("place_id")
    category = data.get("category")

    venues = Business.objects.filter(location__place_id=place_id, category__key=category).order_by(
        "likes")[:10]

    venues = BusinessSerializer(venues, many=True, context={"req": request})

    return Response(venues.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_my_businesses(request):
    businesses = Business.objects.filter(owner=request.user)
    businesses = ShortMyBusinessSerializer(businesses, many=True)
    return Response(businesses.data, status=HTTP_200_OK)


@api_view(["GET"])
@business_authentication
def get_my_business_data(request):
    business = MyBusinessSerializer(request.business)
    return Response(business.data, status=HTTP_200_OK)


class BusinessLikeAPIView(APIView):
    def put(self, request):
        data = request.data
        id = data.get("id")

        try:
            business = Business.objects.get(id=id)
            likes = business.likes

            user = request.user

            params = (user, business)

            if user in likes.all():
                likes.remove(user)
                remove_business_like(*params)
            else:
                likes.add(user)
                add_business_like(*params)

            return Response(status=HTTP_200_OK)

        except Business.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

    # Use POST because need user position
    def post(self, request):
        user = request.user

        venues = []
        queryset = Business.objects.all()

        for venue in queryset:
            if user in venue.likes.all():
                venues.append(venue)

        businesses = BusinessSerializer(venues, many=True, context={"req": request})
        return Response(businesses.data, status=HTTP_200_OK)


# Get business current moment in BusinessDetailScreen
@api_view(["GET"])
def get_business_current_moment(request):
    try:
        business_id = request.query_params.get("business_id")
        business = Business.objects.get(id=business_id)

        moment = EventMoment.objects.filter(business=business).first()
        moment = ShortEventMomentSerializer(moment)

        return Response(moment.data, status=HTTP_200_OK)
    except EventMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


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


class BusinessFeaturesAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, _, endpoint):
        categories = []
        amenities = []

        if endpoint == "both":
            categories = BusinessCategory.objects.all()
            categories = StaticFeatureSerializer(categories, many=True).data

            amenities = Amenity.objects.all()
            amenities = StaticFeatureSerializer(amenities, many=True).data

        if endpoint == "categories":
            categories = BusinessCategory.objects.all()
            categories = StaticFeatureSerializer(categories, many=True).data

        if endpoint == "amenities":
            amenities = Amenity.objects.all()
            amenities = StaticFeatureSerializer(amenities, many=True).data

        return Response({"amenities": amenities, "categories": categories}, status=HTTP_200_OK)


@api_view(["GET", "POST"])
def test_business_auth(request):
    return Response({"content": request.business.name}, status=HTTP_200_OK)
