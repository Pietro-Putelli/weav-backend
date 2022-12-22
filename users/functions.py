from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token

from chat.models import Chat


def get_recent_users_list(user):
    chats = Chat.objects.get_my_chats(user)

    users = []

    for chat in chats:
        sender = chat.sender
        receiver = chat.receiver

        if sender in users or receiver in users:
            continue

        if sender != user:
            users.append(sender)
        if receiver != user:
            users.append(receiver)

    return users


def verify_google_ouath_token(token):
    try:
        user_info = id_token.verify_oauth2_token(token, requests.Request(),
                                                 settings.GOOGLE_CLIENT_ID)
        return user_info
    except ValueError:
        return None
