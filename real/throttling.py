from rest_framework.throttling import UserRateThrottle, BaseThrottle


class UserLoginRateThrottle(BaseThrottle):
    scope = 'login_attempts'

    def allow_request(self, request, view):
        return True


class BusinessRateThrottle(BaseThrottle):
    scope = 'business'

    def allow_request(self, request, view):
        return True
