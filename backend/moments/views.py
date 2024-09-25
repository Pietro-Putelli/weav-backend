import json
from authentication.api_views import BusinessAuthenticationAPIView
from authentication.decorators import authentication_mixin
from business.models import Business
from core.querylimits import QueryLimits
from discussions.utils import create_or_update_discussion
from moments.functions import get_event_moments_by, get_user_moments_by
from moments.models import EventMoment, UserMoment
from moments.serializers import (
    CreateUserMomentSerializer,
    EventMomentDetailSerializer,
    ShortEventMomentSerializer,
    ShortVenueEventPreviewSerializer,
    UserMomentSerializer,
    BusinessEventSerializer,
    CreateOrUpdateEventSerializer,
    ShortEventMomentSerializer,
    ShortMyEventMomentSerializer,
    EventRequestSerializer,
)
from moments.utils import (
    get_event_participants,
)
from profiles.serializers import ShortUserProfileSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_406_NOT_ACCEPTABLE,
)
from rest_framework.views import APIView
from services.date import date_from
from services.utils import cast_to_int
from services.images import moderate_image


@api_view(["POST", "GET"])
def get_user_moments(request):
    moments = get_user_moments_by(request)

    context = {"user": request.user}
    moments = UserMomentSerializer(moments, many=True, context=context)

    return Response(moments.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_user_moments_by_id(request):
    user_id = request.query_params.get("id")

    context = {"user": request.user}

    moments = UserMoment.objects.filter(user__user__uuid=user_id)
    moments = UserMomentSerializer(moments, many=True, context=context)

    return Response(moments.data, status=HTTP_200_OK)


class UserMomentAPIView(APIView):
    def post(self, request):
        data = request.data
        user = request.user

        json_data = json.loads(data.get("data"))
        source = data.get("source")

        serializer = CreateUserMomentSerializer(data=json_data)

        if serializer.is_valid():
            profile = user.profile
            moment = serializer.save(profile, source)

            source = moment.source_url

            # if source:
            #     is_image_valid = True  # moderate_image(source)

            #     if not is_image_valid:
            #         moment.delete()
            #         return Response(status=HTTP_406_NOT_ACCEPTABLE)

            moment = UserMomentSerializer(moment, context={"user": user})

            return Response(moment.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    # Get my moments as USER in 24 hours
    def get(self, request):
        offset = cast_to_int(request.query_params.get("offset"))

        moments = UserMoment.objects.filter(
            user=request.user.profile, created_at__gte=date_from(1)
        )[offset : offset + QueryLimits.MY_MOMENTS]

        context = {"user": request.user}

        moments = UserMomentSerializer(moments, many=True, context=context)

        return Response(moments.data, status=HTTP_200_OK)

    def delete(self, request):
        data = request.query_params
        moment_id = data.get("id")

        UserMoment.objects.filter(user=request.user.profile, uuid=moment_id).delete()

        return Response(status=HTTP_200_OK)


"""
    Get user's friends who replied to moments
"""


@api_view(["GET"])
def get_user_moment_participants(request):
    params = request.query_params

    moment_id = params.get("id")

    offset = cast_to_int(params.get("offset"))
    up_offset = offset + QueryLimits.SEARCH_USERS

    try:
        moment = UserMoment.objects.get(uuid=moment_id)

    except UserMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    users = moment.participants.all()[offset:up_offset]
    users = ShortUserProfileSerializer(users, many=True)

    return Response(users.data, status=HTTP_200_OK)


@api_view(["POST"])
def get_event_moments(request):
    data = request.data

    serializer = EventRequestSerializer(data=data)

    if serializer.is_valid():
        user = request.user
        data = serializer.validated_data

        events = get_event_moments_by(data)
        events = ShortEventMomentSerializer(events, context={"user": user}, many=True)

        return Response(events.data, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_400_BAD_REQUEST)


class EventMomentAPIView(BusinessAuthenticationAPIView):
    def _get_form_data(self, request):
        form_data = request.data
        json_data = form_data.get("data")
        data = json.loads(json_data)

        cover = form_data.get("cover")
        return data, cover, request.business

    def post(self, request):
        data, cover, business = self._get_form_data(request)

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        serializer = CreateOrUpdateEventSerializer(data=data)

        if serializer.is_valid():
            event = serializer.save(business, cover)

            event = BusinessEventSerializer(event)

            return Response(event.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    def put(self, request):
        data, cover, _ = self._get_form_data(request)

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        event_id = data.pop("eventId")

        serializer = CreateOrUpdateEventSerializer(data=data)

        if serializer.is_valid():
            event = serializer.update(event_id, cover)

            event = BusinessEventSerializer(event)

            return Response(event.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        order_by_params = ("date", "time")
        business = request.business

        # First get periodic events
        periodic_events = EventMoment.objects.filter(
            business=business, date__isnull=True
        ).order_by(*order_by_params)

        events = EventMoment.objects.filter(
            business=business, date__isnull=False
        ).order_by(*order_by_params)

        all_events = list(periodic_events) + list(events)

        all_events = ShortVenueEventPreviewSerializer(all_events, many=True)

        return Response(all_events.data, status=HTTP_200_OK)

    def delete(self, request):
        params = request.query_params
        business = request.business

        event_id = params.get("eventId")

        EventMoment.objects.filter(business=business, uuid=event_id).delete()

        return Response(status=HTTP_200_OK)


@api_view(["GET"])
@authentication_mixin
def get_event_moment_detail(request):
    event_id = request.query_params.get("eventId")

    try:
        event = EventMoment.objects.get(uuid=event_id)
        event = EventMomentDetailSerializer(event, context={"user": request.user})

        return Response(event.data, status=HTTP_200_OK)
    except EventMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


"""
    When the user go to an event they join a discussion
"""


@api_view(["PUT"])
def user_go_to_event(request):
    event_id = request.data.get("id")

    try:
        event = EventMoment.objects.get(uuid=event_id)

        profile = request.user.profile
        participants = event.participants

        if profile in participants.all():
            participants.remove(profile)
            is_going = False
        else:
            participants.add(profile)
            is_going = True

        discussion = create_or_update_discussion(event, profile, is_going)

    except EventMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    return Response(
        {"is_going": is_going, "discussion": discussion}, status=HTTP_200_OK
    )


@api_view(["GET"])
def get_event_moment_participants(request):
    params = request.query_params

    event_id = params.get("eventId")
    offset = cast_to_int(params.get("offset"))
    limit = cast_to_int(params.get("limit"))

    profile = request.user.profile

    participants = get_event_participants(event_id, profile, offset, limit)

    if participants is None:
        return Response(status=HTTP_404_NOT_FOUND)

    return Response(participants, status=HTTP_200_OK)


@api_view(["POST"])
def get_my_events(request):
    profile = request.user.profile

    serializer = EventRequestSerializer(data=request.data)

    if serializer.is_valid():
        data = serializer.validated_data

        offset = data.get("offset")
        up_offset = offset + 8

        events = EventMoment.objects.get_mine(profile).order_by("date")[
            offset:up_offset
        ]

        events = ShortMyEventMomentSerializer(events, many=True)

        return Response(events.data, status=HTTP_200_OK)

    print(serializer.errors)

    return Response(status=HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_business_moments(request):
    user = request.user
    params = request.query_params

    business_id = params.get("businessId")
    offset = cast_to_int(params.get("offset"))
    up_offset = offset + 8

    business = Business.objects.filter(uuid=business_id).first()

    if business is None:
        return Response(status=HTTP_404_NOT_FOUND)

    moments = UserMoment.objects.filter(business_tag=business).order_by("-created_at")[
        offset:up_offset
    ]

    moments = UserMomentSerializer(moments, context={"user": user}, many=True)

    return Response(moments.data, status=HTTP_200_OK)
