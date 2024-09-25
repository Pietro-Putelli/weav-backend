from rest_framework import permissions
from rest_framework.authtoken.models import Token

from business.models import BusinessToken


class PermissionMixin(permissions.BasePermission):
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


class BusinessOwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if raw_token is None:
            return False

        request.user = None

        token_key = raw_token.replace("Token ", "")
        return BusinessToken.objects.filter(key=token_key).exists()
