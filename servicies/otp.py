import shortuuid

# from phone_verify.services import PhoneVerificationService

from core.stringvalidators import get_username_type
from users.email import TokenVerificationEmail


def get_otp_code():
    s = shortuuid.ShortUUID(alphabet="0123456789")
    return s.random(length=5)


def send_otp_to_username(username):
    if username is None:
        return None

    from users.models import TokenCode

    token = TokenCode.objects.update_or_create(username=username)

    username_type = get_username_type(username)

    if username_type == "email":
        TokenVerificationEmail(context={"code": token.code}).send(to=[username])
        return token

    elif username_type == "phone":
        service = None  # PhoneVerificationService(phone_number=username)
        try:
            service.send_verification(username, token.code)
            return token

        except service.backend.exception_class:
            pass

    return None
