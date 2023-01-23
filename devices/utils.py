import asyncio
import json
import time

import httpx
import jwt
import requests
from django.conf import settings

from business.models import Business
from chat.models import ChatMessageReactions
from profiles.serializers import ShortUserProfileSerializer


class NotificationType:
    MESSAGE = "message"
    BUSINESS_MESSAGE = "business_message"
    DISCUSSION_MESSAGE = "discussion_message"
    FRIEND_REQUEST = "friend_request"
    FRIEND_REQUEST_ACCEPTED = "friend_request_accepted"
    MOMENT_MENTION = "moment_mention"
    MOMENT_BUSINESS_MENTION = "moment_business_mention"
    NEW_EVENT = "new_event"
    EVENT_REPOST = "event_repost"


def format_chat_notification(sender, message):
    username = sender.username
    receiver = message.receiver

    user_profile = message.user_profile
    business_profile = message.business_profile

    user_moment = message.moment
    event_moment_slice = message.event

    reaction = message.reaction

    msg_content = message.content

    content = None

    if msg_content is not None and reaction is None:
        content = "New message"
    elif user_profile:
        content = f"Shared {user_profile.username}'s profile"
    elif business_profile:
        content = f"🍸 Shared {business_profile.name}'s profile"
    elif user_moment:
        content = f"Shared {user_moment.user.username}'s moment"
    elif event_moment_slice:
        content = f"🎉 Shared {event_moment_slice.moment.title} event"
    elif reaction == ChatMessageReactions.HEY:
        content = "✌️ Hey"
    elif reaction == ChatMessageReactions.EMOJI:
        content = f"{msg_content} Reacted to your moment"

    from chat.serializers import ChatSerializer
    chat = ChatSerializer(message.chat, context={"user": receiver}).data

    return username, content, chat


def format_business_chat_notification(sender, message):
    is_business = isinstance(sender, Business)
    content = "New message"

    if is_business:
        username = "🍸 " + sender.name
    else:
        username = f"[{message.chat.business.name}]: " + sender.username

    from chat.serializers import BusinessChatSerializer
    chat = BusinessChatSerializer(message.chat, context={"is_user": is_business}).data

    return username, content, chat


def send_ios_notification(device_token, sender, message, type):
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

    title, body = "Weav", None

    payload = {}

    if type == NotificationType.MESSAGE:
        title, body, chat = format_chat_notification(sender, message)
        payload["chat"] = chat

    elif type == NotificationType.BUSINESS_MESSAGE:
        title, body, chat = format_business_chat_notification(sender, message)
        payload["chat"] = chat

    elif type == NotificationType.FRIEND_REQUEST:
        title = sender.username
        body = "Sent you a friend request"
        payload["user"] = ShortUserProfileSerializer(sender).data

    elif type == NotificationType.FRIEND_REQUEST_ACCEPTED:
        title = sender.username
        body = "👋 Accepted your friend request"
        payload["user_id"] = sender.uuid

    elif type == NotificationType.MOMENT_MENTION:
        title = f"{sender.username}"
        body = "Mentioned you in a moment"
        payload["moment_id"] = message.uuid

    elif type == NotificationType.MOMENT_BUSINESS_MENTION:
        # In this case the message is the moment
        title = f"[{message.business_tag.name}]: {sender.username}"
        body = "Mentioned you in a moment"
        payload["moment_id"] = message.uuid

    elif type == NotificationType.DISCUSSION_MESSAGE:
        discussion = message.discussion

        title = f"💬 {discussion.event.title}"
        body = f"{sender.username}: {message.content}"
        payload["discussion_id"] = discussion.id

    elif type == NotificationType.NEW_EVENT:
        title = f"🎉 {message.title}"
        body = f"{sender.name} created a new event"
        payload["event_id"] = message.uuid

    elif type == NotificationType.EVENT_REPOST:
        title = f"[{message.moment.business.name}]: {sender.username}"
        body = "Reposted your event"

    # If the body does not exists, don't send the notification
    if body is None:
        return False

    payload = {
        "aps": {
            "alert": {
                "title": title,
                "body": body,
            },
            "badge": 1,
            "sound": "default",
        },
        **payload
    }

    response = asyncio.run(client.post(
        "https://api.sandbox.push.apple.com:443/3/device/{}".format(device_token),
        json=payload,
        headers=headers,
    ))

    return response.status_code == 200


def send_android_notification(device_token, user, message):
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


'''
    Use to set is_logged when the user logs-in
'''
