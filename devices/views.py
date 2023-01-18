from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from devices.models import Device


@api_view(["PUT"])
def logout(request):
    Device.objects.filter(user=request.user).update(is_logged=False)
    return Response(status=HTTP_200_OK)
