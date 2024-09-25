import asyncio
import json

import httpx
import requests
from django.conf import settings

from business.models import Business
from chat.models import ChatMessageReactions
from discussions.serializers import EventDiscussionSerializer
from languages.language import get_language_content
from profiles.models import UserProfile
from profiles.serializers import ShortUserProfileSerializer
from services.apple_token import get_apns_apple_secret


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
    NEW_BUSINESS = "new_business"

    WEEKLY_UPDATES = "weekly_updates"

    # Business Side
    BUSINESS_APPROVED = "business_approved"
    NEW_INSIGHTS = "new_insights"

    SPOT_REPLY = "spot_reply"


def format_chat_notification(sender, message):
    sender_username = sender.username
    receiver = message.receiver

    user_profile = message.user_profile
    business_profile = message.business_profile

    user_moment = message.moment
    event = message.event

    reaction = message.reaction

    msg_content = message.content

    content = None

    language_content, language = get_language_content(receiver)

    if msg_content is not None and reaction is None:
        content = msg_content
    elif user_profile:
        username = user_profile.username

        content = f"Shared {username}'s profile"

        if language == "it":
            content = f"Ha condiviso il profilo di {username}"

    elif business_profile:
        name = business_profile.name

        content = f"Shared {name}'s profile"

        if language == "it":
            content = f"Ha condiviso il profilo di {name}"

    elif user_moment:
        username = user_moment.user.username

        if receiver.id == user_moment.user.id:
            content = f"Replied to your moment"
            if language == "it":
                content = f"Ha risposto al tuo momento"
        else:
            content = f"Shared {username}'s moment"
            if content == "it":
                content = f"Ha condiviso il momento di {username}"

    elif event:
        event_title = event.title

        content = f"🍸 Shared {event_title}"

        if language == "it":
            content = f"🍸 Ha condiviso {event_title}"

    elif reaction == ChatMessageReactions.HEY:
        content = "✌️ Hey"
    elif reaction == ChatMessageReactions.EMOJI:
        content = f"{msg_content} {language_content['reacted_to_moment']}"

    from chat.serializers import ChatSerializer

    chat = ChatSerializer(message.chat, context={"user": receiver}).data

    return sender_username, content, chat


def format_business_chat_notification(sender, message):
    is_business = isinstance(sender, Business)

    if is_business:
        username = "🍸 " + sender.name
    else:
        username = f"[{message.chat.business.name}]: " + sender.username

    content = message.content

    from chat.serializers import BusinessChatSerializer

    chat = BusinessChatSerializer(
        message.chat, context={"is_user": is_business}).data

    return username, content, chat


def format_notification(notification_type, sender, message):
    title, subtitle, body = "Weav", "", ""

    payload = {}

    receiver = None

    if hasattr(message, "receiver"):
        receiver = message.receiver
    elif hasattr(message, "business"):
        receiver = message.business.owner.user
    elif hasattr(message, "user"):
        receiver = message.user
    else:
        receiver = message

    language_content, _ = get_language_content(receiver)

    if notification_type == NotificationType.MESSAGE:
        title, body, chat = format_chat_notification(sender, message)
        payload["chat"] = chat

    elif notification_type == NotificationType.BUSINESS_MESSAGE:
        title, body, chat = format_business_chat_notification(sender, message)
        payload["chat"] = chat

    elif notification_type == NotificationType.FRIEND_REQUEST:
        title = sender.username
        body = f"❤️ {language_content['sent_friend_request']}"
        payload["user"] = ShortUserProfileSerializer(sender).data

    elif notification_type == NotificationType.FRIEND_REQUEST_ACCEPTED:
        title = sender.username
        body = f"👋 {language_content['accepted_friend_request']}"
        payload["user_id"] = sender.user.uuid

    elif notification_type == NotificationType.MOMENT_MENTION:
        title = sender.username
        body = f"🔥 {language_content['mentioned_you_in_moment']}"
        payload["moment_id"] = message.uuid

    elif notification_type == NotificationType.DISCUSSION_MESSAGE:
        discussion = message.discussion

        title = f"💬 {discussion.event.title}"
        body = f"{sender.username}: {message.content}"
        payload["chat"] = EventDiscussionSerializer(discussion).data

    elif notification_type == NotificationType.NEW_EVENT:
        title = f"🍸 {message.title}"
        body = f"{sender.name} {language_content['created_new_event']}"
        payload["event_id"] = message.uuid

    elif notification_type == NotificationType.BUSINESS_APPROVED:
        title = f"🚀 {language_content['welcome_to']} Weav"
        subtitle = f"Hey {message.owner.user.name} {language_content['your_business_approved']}"

    elif notification_type == NotificationType.WEEKLY_UPDATES:
        title = f"🔥 This Weekend"
        subtitle = language_content["weekly_updates"]
        payload["weekly_updates"] = True

    elif notification_type == NotificationType.SPOT_REPLY:
        title = f"🏹 {sender.username} {language_content['replied_to_your_spot']}"
        payload["spot_id"] = message.uuid

    return title, subtitle, body, payload


def send_ios_notification(device_token, type, sender=None, message=None):
    token = get_apns_apple_secret()

    client = httpx.AsyncClient(http2=True)

    headers = {
        "Content-Type": "application/json",
        "apns-topic": settings.IOS_APP_BUNDLE_ID,
        "Authorization": f"bearer {token}",
    }

    title, subtitle, body, payload = format_notification(type, sender, message)

    if body is None:
        return False

    payload = {
        "aps": {
            "alert": {"title": title, "body": body, "subtitle": subtitle},
            "badge": 1,
            # "sound": "weav-sound.caf",
        },
        **payload,
    }

    api_url = "api.push.apple.com"

    if settings.DEBUG:
        api_url = "api.sandbox.push.apple.com"

    response = asyncio.run(
        client.post(
            f"https://{api_url}:443/3/device/{device_token}",
            json=payload,
            headers=headers,
        )
    )

    return response.status_code == 200


def send_android_notification(device_token, type, sender, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "key=" + settings.FIREBASE_API_KEY,
    }

    title, subtitle, body, payload = format_notification(type, sender, message)

    if body is None:
        return False

    body = {
        "notification": {"title": title, "body": body},
        "to": device_token,
        "priority": "high",
        **payload,
    }

    json_body = json.dumps(body)

    response = requests.post(
        "https://fcm.googleapis.com/fcm/send", headers=headers, data=json_body
    )

    return response.status_code == 200
