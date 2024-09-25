import jwt
import time
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


def get_apns_apple_secret():
    file = open(settings.APNS_AUTH_KEY)
    secret = file.read()

    algorithm = "ES256"

    token = jwt.encode(
        {"iss": settings.IOS_TEAM_ID, "iat": time.time()},
        secret,
        algorithm=algorithm,
        headers={
            "alg": algorithm,
            "kid": settings.APNS_KEY_ID,
        },
    )

    return token


def get_sign_in_with_apple_secret():
    file = open(settings.SIGN_IN_AUTH_KEY)
    secret_key = file.read()

    headers = {
        'kid': settings.SIGN_IN_KEY_ID,
        'alg': 'ES256'
    }

    payload = {
        'iss': settings.IOS_TEAM_ID,
        'iat': timezone.now(),
        'exp': timezone.now() + timedelta(days=180),
        'aud': 'https://appleid.apple.com',
        'sub': settings.IOS_APP_BUNDLE_ID,
    }

    client_secret = jwt.encode(
        payload,
        secret_key,
        algorithm='ES256',
        headers=headers
    )

    return client_secret, settings.IOS_APP_BUNDLE_ID
