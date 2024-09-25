import binascii
import os
from django.db.models import Count
from moments.models import UserMoment
from services.utils import flatten_list
from spots.models import Spot
from chat.models import Chat
from profiles.models import UserFriend, UserFriendRequest
from rest_framework.response import Response


class FriendShipState:
    # I and the user are friends
    FRIEND = "friend"

    # I requested the friendship with a user
    MY_REQUEST = "my-request"

    # Another user requested me to be friend
    USER_REQUEST = "user-request"

    # There's no relationships between the users
    NONE = "none"


# my_user = request.user and user is the profile I'm requesting
def get_friendship_state(my_user, user):
    are_friends = UserFriend.objects.are_friends(my_user, user)

    if are_friends:
        return FriendShipState.FRIEND

    queryset = UserFriendRequest.objects

    my_request = queryset.filter(user=my_user, friend=user)

    if my_request.exists():
        return FriendShipState.MY_REQUEST

    user_request = queryset.filter(user=user, friend=my_user)

    if user_request.exists():
        return FriendShipState.USER_REQUEST

    return FriendShipState.NONE


def get_chats_recent(user):
    from chat.models import Chat

    recent_chats = Chat.objects.get_recent(user)[:8]

    users = []
    for chat in recent_chats:
        sender = chat.sender
        receiver = chat.receiver

        if user == sender:
            users.append(receiver)
        else:
            users.append(sender)

    return users


def handle_blocked_user(user, blocked_user):
    args = (user, blocked_user)

    UserFriend.objects.remove_blocked(*args)
    UserFriendRequest.objects.remove_blocked(*args)
    Chat.objects.remove_blocked(*args)


def generate_hex_token():
    return binascii.hexlify(os.urandom(20)).decode()


"""
    Get user profile info once open the app
"""


def get_profile_info(profile):
    requests = UserFriendRequest.objects.filter(friend=profile).values("id")
    moments = UserMoment.objects.get_moments_where_im_tagged(profile).values("id")

    spot_replies = list(
        Spot.objects.filter(profile=profile)
        .annotate(count=Count("replies"))
        .values("uuid", "count")
    )

    spot_replies = [f"{spot['uuid']}:{spot['count']}" for spot in spot_replies]

    requests = flatten_list(requests)
    moments = flatten_list(moments)

    return {
        "friendRequests": list(requests),
        "mentionedMoments": list(moments),
        "spotReplies": spot_replies,
    }
