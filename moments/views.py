import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, \
    HTTP_406_NOT_ACCEPTABLE
from rest_framework.views import APIView

from business.authentication import BusinessAuthenticationAPIView, business_authentication
from discussions.utils import create_or_update_discussion
from moments.functions import get_event_moments_by, get_user_moments_by
from moments.models import EventMoment, UserMoment, EventMomentSlice
from moments.serializers import UserMomentSerializer, EventMomentSerializer, \
    CreateUserMomentSerializer, ShortEventMomentSerializer, EventMomentDetailSerializer, \
    CurrentEventMomentSerializer
from moments.utils import get_validated_sources, create_event_moment, update_event_moment, \
    get_event_participants, get_grouped_my_events
from servicies.date import date_from
from servicies.utils import cast_to_int


@api_view(["POST", "GET"])
def get_user_moments(request):
    moments = get_user_moments_by(request)
    moments = UserMomentSerializer(moments, many=True)

    return Response(moments.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_user_moments_by_id(request):
    user_id = request.query_params.get("id")

    moments = UserMoment.objects.filter(user__uuid=user_id)
    moments = UserMomentSerializer(moments, many=True)

    return Response(moments.data, status=HTTP_200_OK)


class UserMomentAPIView(APIView):
    def post(self, request):
        data = request.data

        json_data = json.loads(data.get("data"))
        source = data.get("source")

        serializer = CreateUserMomentSerializer(data=json_data)

        if serializer.is_valid():
            moment = serializer.save(source=source, user=request.user)

            if moment is None:
                return Response(status=HTTP_406_NOT_ACCEPTABLE)

            moment = UserMomentSerializer(moment)

            return Response(moment.data, status=HTTP_200_OK)

        print(serializer.errors)

        return Response(status=HTTP_400_BAD_REQUEST)

    # Get my moments as USER in 24 hours
    def get(self, request):
        moments = UserMoment.objects.filter(user=request.user, created_at__gte=date_from(20))
        moments = UserMomentSerializer(moments, many=True)

        return Response(moments.data, status=HTTP_200_OK)

    def delete(self, request):
        data = request.query_params
        moment_id = data.get("id")

        UserMoment.objects.filter(user=request.user, uuid=moment_id).delete()

        return Response(status=HTTP_200_OK)


@api_view(["POST", "GET"])
def get_event_moments(request):
    moments = get_event_moments_by(request)
    moments = ShortEventMomentSerializer(moments, many=True)

    return Response(moments.data, status=HTTP_200_OK)


class EventMomentAPIView(BusinessAuthenticationAPIView):
    def _get_form_data(self, request):
        form_data = request.data
        data = json.loads(form_data.get("data"))

        return form_data, data, request.business

    def post(self, request):
        form_data, data, business = self._get_form_data(request)

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        slices_count = data.pop("slices_count")
        sources = get_validated_sources(form_data, slices_count)

        if len(sources) == 0:
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        moment = create_event_moment(business, data, sources)

        if moment is not None:
            moment = CurrentEventMomentSerializer(moment)
            return Response(moment.data, status=HTTP_200_OK)

        return Response(status=HTTP_400_BAD_REQUEST)

    def put(self, request):
        form_data, data, business = self._get_form_data(request)

        if data is None:
            return Response(status=HTTP_404_NOT_FOUND)

        slices_count = data.pop("slices_count")
        sources = get_validated_sources(form_data, slices_count)

        if slices_count != 0 and len(sources) == 0:
            return Response(status=HTTP_406_NOT_ACCEPTABLE)

        moment = update_event_moment(business, data, sources)

        if moment:
            moment = CurrentEventMomentSerializer(moment)
            return Response(moment.data, status=HTTP_200_OK)

        return Response(status=HTTP_400_BAD_REQUEST)

    def get(self, request):
        moments = EventMoment.objects.filter(business=request.business).order_by("-created_at")
        moments = EventMomentSerializer(moments, many=True)

        return Response(moments.data, status=HTTP_200_OK)

    def delete(self, request):
        data = request.data
        moment_id = data.get("id")

        try:
            moment = EventMoment.objects.get(uuid=moment_id)
            moment.delete()

            return Response(status=HTTP_200_OK)
        except EventMoment.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)


class CurrentEventMomentAPIView(BusinessAuthenticationAPIView):
    def get(self, request):
        moment = EventMoment.objects.filter(business=request.business,
                                            created_at__gte=date_from(10)).first()
        data = {}
        if moment is not None:
            data = CurrentEventMomentSerializer(moment).data

        return Response(data, status=HTTP_200_OK)

    # Use both to delete single slice and entire moment
    def delete(self, request):
        params = request.query_params

        slice_id = params.get("id")
        is_deleting_moment = slice_id is None

        if not is_deleting_moment:
            EventMomentSlice.objects.filter(id=slice_id).delete()
            EventMoment.objects.delete_current_if_has_no_slices(request.business)
        else:
            EventMoment.objects.delete_current(request.business)

        return Response(status=HTTP_200_OK)


@api_view(["GET"])
def get_event_moment_detail(request):
    event_id = request.query_params.get("id")

    try:
        event = EventMoment.objects.get(uuid=event_id)
        event = EventMomentDetailSerializer(event, context={"user": request.user})

        return Response(event.data, status=HTTP_200_OK)
    except EventMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)


'''
    When the user go to an event they join a discussion
'''


@api_view(["PUT"])
def user_go_to_event(request):
    event_id = request.data.get("id")

    try:
        event = EventMoment.objects.get(uuid=event_id)

        user = request.user
        participants = event.participants

        if user in participants.all():
            participants.remove(user)
            is_going = False
        else:
            participants.add(user)
            is_going = True

        discussion = create_or_update_discussion(event, user, is_going)


    except EventMoment.DoesNotExist:
        return Response(status=HTTP_404_NOT_FOUND)

    return Response({"is_going": is_going, "discussion": discussion}, status=HTTP_200_OK)


# Get all USER-MOMENTS where the business is tagged in latest 24 hours.
@api_view(["GET"])
@business_authentication
def get_tagged_user_moments(request):
    params = request.query_params
    offset = cast_to_int(params.get("offset"))
    up_offset = offset + 8

    moments = UserMoment.objects.filter(created_at__gte=date_from(10),
                                        business_tag=request.business)[offset:up_offset]

    moments = UserMomentSerializer(moments, many=True)
    return Response(moments.data, status=HTTP_200_OK)


@api_view(["GET"])
@business_authentication
def get_archived_event_moments(request):
    params = request.query_params

    offset = cast_to_int(params.get("offset"))
    up_offset = offset + 8

    moments = EventMoment.objects.filter(business=request.business, created_at__lte=date_from(1))[
              offset:up_offset]

    moments = EventMomentSerializer(moments, many=True)
    return Response(moments.data, status=HTTP_200_OK)


'''
    Get all my friends who go to the event
'''


@api_view(["GET"])
def get_event_moment_participants(request):
    params = request.query_params

    event_id = params.get("id")
    offset = cast_to_int(params.get("offset"))
    limit = cast_to_int(params.get("limit"))

    participants = get_event_participants(event_id, request.user, offset, limit)

    if participants is None:
        return Response(status=HTTP_404_NOT_FOUND)

    return Response(participants, status=HTTP_200_OK)


@api_view(["GET"])
def get_my_events(request):
    events = get_grouped_my_events(request.user)
    return Response(events, status=HTTP_200_OK)
