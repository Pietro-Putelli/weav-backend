from rest_framework.throttling import SimpleRateThrottle


class UnAuthenticatedThrottle(SimpleRateThrottle):
    scope = 'unauthenticated_user'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)}

class BusinessRateThrottle(SimpleRateThrottle):
    scope = "business"

    def get_cache_key(self, request, view):
        user = request.user

        if user is not None and user.is_authenticated:
            ident = request.user.pk
        elif hasattr(request, "business"):
            ident = request.business.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
