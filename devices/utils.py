import time

import httpx
import jwt
from django.conf import settings


async def send_ios_notification(device_token, user, message):
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

    client = httpx.AsyncClient(http2=True)

    headers = {
        "Content-Type": "application/json",
        "apns-topic": "com.app.weav",
        "Authorization": f"bearer {token}",
    }

    payload = {
        "aps": {
            "alert": {
                "title": user.username,
                "body": message.content,
            },
            "badge": 1, "sound": "default",
        }
    }

    response = await client.post(
        "https://api.sandbox.push.apple.com:443/3/device/{}".format(device_token),
        json=payload,
        headers=headers,
    )

    return response.status_code == 200


def send_android_notification(device_token):
    return ""
