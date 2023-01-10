from rest_framework import authentication, permissions, exceptions
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    permission_classes,
    authentication_classes,
    throttle_classes,
)
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from business.models import BusinessToken
from core.decorators import composed
from throttling.throttlers import BusinessRateThrottle


class UserOrBusinessAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if not raw_token:
            return None

        token_key = raw_token.replace("Token ", "")

        user_token = Token.objects.filter(key=token_key).first()

        if user_token is not None:
            user = user_token.user
            request.user = user

            return user, None

        business_token = BusinessToken.objects.filter(key=token_key).first()

        if business_token is not None:
            business = business_token.business
            request.business = business

            return business, None
        raise exceptions.AuthenticationFailed('No such user or business')



class UserOrBusinessPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if raw_token is None:
            return False

        token_key = raw_token.replace("Token ", "")

        user_token = Token.objects.filter(key=token_key).first()

        if user_token is not None:
            return True

        business_token = BusinessToken.objects.filter(key=token_key).first()

        if business_token is not None:
            return True

        return False



authentication_mixin = composed(permission_classes([UserOrBusinessPermission]),
                                authentication_classes([UserOrBusinessAuthentication]),
                                throttle_classes([UserRateThrottle, BusinessRateThrottle]))



class AuthenticationMixinAPIView(APIView):
    permission_classes = (UserOrBusinessPermission,)
    authentication_classes = (UserOrBusinessAuthentication,)
    throttle_classes = (UserRateThrottle, BusinessRateThrottle)
