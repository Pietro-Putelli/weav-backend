from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from chances.models import UserChance


class ChanceAPIView(APIView):
    def delete(self, request):
        chance_id = request.query_params.get("id")

        UserChance.objects.filter(id=chance_id).delete()

        return Response(status=HTTP_200_OK)
