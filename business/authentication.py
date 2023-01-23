from rest_framework import authentication, permissions, exceptions
from rest_framework.decorators import permission_classes, authentication_classes, throttle_classes
from rest_framework.views import APIView

from business.models import BusinessToken
from core.decorators import composed
from throttling.throttlers import MixinRateThrottle


class BusinessOwnerAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if not raw_token:
            return None

        token_key = raw_token.replace("Token ", "")

        try:
            token = BusinessToken.objects.get(key=token_key)
            business = token.business

            request.user = None
            request.business = business

        except BusinessToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such business')

        return business, None


class BusinessOwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if raw_token is None:
            return False

        request.user = None

        token_key = raw_token.replace("Token ", "")
        return BusinessToken.objects.filter(key=token_key).exists()


business_authentication = composed(permission_classes([BusinessOwnerPermission]),
                                   authentication_classes([BusinessOwnerAuthentication]),
                                   throttle_classes([MixinRateThrottle]))


class BusinessAuthenticationAPIView(APIView):
    permission_classes = (BusinessOwnerPermission,)
    authentication_classes = (BusinessOwnerAuthentication,)
    throttle_classes = (MixinRateThrottle,)
