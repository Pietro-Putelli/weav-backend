from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from authentication.api_views import AuthenticationMixinAPIView
from authentication.decorators import authentication_mixin
from devices.models import Device


class DeviceAPIView(AuthenticationMixinAPIView):
    def put(self, request):
        data = request.data
        user = request.user

        token = data.get("token", None)
        os_type = data.get("os_type", None)

        if token is not None:
            Device.objects.update_or_create(user, os_type, token)
        else:
            Device.objects.filter(user=user).update(**data)

        return Response(status=HTTP_200_OK)


@api_view(["PUT"])
@authentication_mixin
def logout(request):
    Device.objects.logout(request.user)

    return Response(status=HTTP_200_OK)
