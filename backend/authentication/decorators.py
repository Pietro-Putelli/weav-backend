from rest_framework.decorators import permission_classes, authentication_classes, throttle_classes

from core.decorators import composed
from throttling.throttlers import MixinRateThrottle
from .authentication import AuthenticationMixin, BusinessOwnerAuthentication
from .permissions import PermissionMixin, BusinessOwnerPermission

authentication_mixin = composed(permission_classes([PermissionMixin]),
                                authentication_classes([AuthenticationMixin]),
                                throttle_classes([MixinRateThrottle]))

business_authentication = composed(permission_classes([BusinessOwnerPermission]),
                                   authentication_classes([BusinessOwnerAuthentication]),
                                   throttle_classes([MixinRateThrottle]))
