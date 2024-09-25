from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from throttling.throttlers import MixinRateThrottle
from .authentication import AuthenticationMixin, BusinessOwnerAuthentication
from .permissions import PermissionMixin, BusinessOwnerPermission


class AuthenticationMixinAPIView(APIView):
    permission_classes = (PermissionMixin,)
    authentication_classes = (AuthenticationMixin,)
    throttle_classes = (MixinRateThrottle,)


class AuthenticationMixinViewSet(ViewSet):
    permission_classes = (PermissionMixin,)
    authentication_classes = (AuthenticationMixin,)
    throttle_classes = (MixinRateThrottle,)


class BusinessAuthenticationAPIView(APIView):
    permission_classes = (BusinessOwnerPermission,)
    authentication_classes = (BusinessOwnerAuthentication,)
    throttle_classes = (MixinRateThrottle,)
