from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from core.authentication import authentication_mixin
from devices.models import Device


@api_view(["PUT"])
def logout(request):
    Device.objects.filter(user=request.user).update(is_logged=False)
    return Response(status=HTTP_200_OK)


@api_view(["PUT"])
@authentication_mixin
def set_device_token(request):
    data = request.data
    token = data.get("token")

    Device.objects.update_or_create(user=request.user, token=token)

    return Response(status=HTTP_200_OK)
