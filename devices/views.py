from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.decorators import api_view

from devices.models import Device


@api_view(['GET'])
def send_notification(request):
    device = Device.objects.get(user=request.user)
    device.send_notification()
    return Response(status=HTTP_200_OK)
