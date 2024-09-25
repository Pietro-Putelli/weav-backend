from business.models import BusinessToken
from rest_framework.authtoken.models import Token
from rest_framework import authentication, exceptions


class AuthenticationMixin(authentication.BaseAuthentication):
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

            return business.owner.user, None
        raise exceptions.AuthenticationFailed('No such user or business')


class BusinessOwnerAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        raw_token = request.META.get('HTTP_AUTHORIZATION')

        if not raw_token:
            return None

        token_key = raw_token.replace("Token ", "")

        try:
            token = BusinessToken.objects.get(key=token_key)
            business = token.business

            request.business = business

        except BusinessToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such business')

        return business.owner.user, None
