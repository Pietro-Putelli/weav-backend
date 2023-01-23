from rest_framework.throttling import SimpleRateThrottle

from users.models import User


class UnAuthenticatedThrottle(SimpleRateThrottle):
    scope = 'unauthenticated_user'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)}


class MixinRateThrottle(SimpleRateThrottle):
    scope = "mixin"

    def get_cache_key(self, request, view):
        user = request.user

        if isinstance(user, User) and user.is_authenticated:
            ident = request.user.pk
        elif hasattr(request, "business"):
            ident = request.business.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
