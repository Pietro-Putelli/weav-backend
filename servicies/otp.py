import shortuuid


# from phone_verify.services import PhoneVerificationService


def get_otp_code():
    s = shortuuid.ShortUUID(alphabet="0123456789")
    return s.random(length=5)
