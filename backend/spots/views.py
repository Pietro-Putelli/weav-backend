from business.serializers import ShortBusinessSerializer
from profiles.serializers import ShortUserProfileSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from services.utils import cast_to_int
from .models import Spot
from .serializers import CreateSpotSerializer, SpotSerializer
from .utils import send_spot_reply_notification


class SpotsAPIView(APIView):
    def post(self, request):
        data = request.data

        user = request.user
        profile = user.profile

        serializer = CreateSpotSerializer(data=data)

        if serializer.is_valid():
            spot = serializer.save(profile)
            spot = SpotSerializer(spot, context={"user": user})

            return Response(spot.data, status=HTTP_200_OK)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    # Get a spot by business id

    def get(self, request):
        params = request.query_params

        business_id = params.get("businessId")
        offset = cast_to_int(params.get("offset"))
        up_offset = offset + 8

        spots = Spot.objects.filter(business__uuid=business_id).order_by("-created_at")[
            offset:up_offset
        ]

        spots = SpotSerializer(spots, many=True, context={"user": request.user})

        return Response(spots.data, status=HTTP_200_OK)

    def delete(self, request):
        spotId = request.query_params.get("spotId")

        Spot.objects.filter(uuid=spotId).delete()

        return Response(status=HTTP_200_OK)


@api_view(["PUT"])
def reply_spot(request):
    data = request.data

    spot_id = data.get("spotId")
    user = request.user
    profile = user.profile

    spot = Spot.objects.filter(uuid=spot_id).first()

    if spot is not None:
        spot.replies.add(profile)
        spot.save()

        send_spot_reply_notification(profile, spot)

    return Response(status=HTTP_200_OK)


@api_view(["GET"])
def get_my_spots(request):
    profile = request.user.profile

    spots = Spot.objects.filter(profile=profile).order_by("-created_at")

    spots = SpotSerializer(spots, many=True, context={"user": request.user})

    return Response(spots.data, status=HTTP_200_OK)


@api_view(["GET"])
def get_spot_replies(request):
    params = request.query_params

    spot_id = params.get("spotId")
    offset = cast_to_int(params.get("offset"))

    spot = Spot.objects.filter(uuid=spot_id).first()

    if spot is not None:
        profiles = spot.replies.all()
        profiles_count = profiles.count()
        profiles = profiles[offset : offset + 8]

        profiles = ShortUserProfileSerializer(profiles, many=True)

        business = ShortBusinessSerializer(spot.business)

        if offset == 0:
            response = {
                "replies": profiles.data,
                "business": business.data,
                "count": profiles_count,
            }
        else:
            response = profiles.data

        return Response(response, status=HTTP_200_OK)

    return Response(status=HTTP_400_BAD_REQUEST)
