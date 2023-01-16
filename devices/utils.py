import asyncio
import json
import time

import httpx
import jwt
import requests
from django.conf import settings

from business.models import Business
from chat.models import ChatMessageReactions


def get_notifications_body(sender, message):
    is_business = isinstance(sender, Business)
    content = ""

    if is_business:
        username = "🍸 " + sender.name
    else:
        username = sender.username

        user_profile = message.user_profile
        business_profile = message.business_profile

        user_moment = message.user_moment
        event_moment_slice = message.event_moment

        reaction = message.reaction

        msg_content = message.content

        if msg_content is not None and reaction is None:
            content = msg_content
        elif user_profile:
            content = f"Shared {user_profile.username}'s profile"
        elif business_profile:
            content = f"Shared {business_profile.name}'s profile"
        elif user_moment:
            content = f"Shared {user_moment.user.username}'s moment"
        elif event_moment_slice:
            content = f"Shared {event_moment_slice.moment.title} event"
        elif reaction == ChatMessageReactions.HEY:
            content = "✌️ Hey"
        elif reaction == ChatMessageReactions.EMOJI:
            content = f"{msg_content} Reacted to your moment"

    return username, content


# user can be User or Business
def send_ios_notification(device_token, username, msg_body):
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
                "title": username,
                "body": msg_body,
            },
            "badge": 1, "sound": "default",
        }
    }

    response = asyncio.run(client.post(
        "https://api.sandbox.push.apple.com:443/3/device/{}".format(device_token),
        json=payload,
        headers=headers,
    ))

    return response.status_code == 200


def send_android_notification(device_token, user, message, is_business=False):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=" + settings.ANDROID_API_KEY,
    }

    body = {
        "notification": {"title": user.username, "body": message.content},
        "to": device_token,
        "priority": "high",
    }

    json_body = json.dumps(body)

    response = requests.post(
        "https://fcm.googleapis.com/fcm/send", headers=headers, data=json_body
    )

    return response.status_code == 200
