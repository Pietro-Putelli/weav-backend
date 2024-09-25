import json
from asgiref.sync import async_to_sync
from profiles.utils import get_profile_info
from .serializers import AlignUserData
from users.models import User
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from .actions import SocketActions
from django.db.models.query_utils import Q


def get_channel_name(profile):
    return f"user.{profile.user.uuid}"


def send_data_to_socket_channel(channel_name, action, data):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        channel_name,
        {
            "type": "send_data",
            "action": action,
            "content": data,
        },
    )


@database_sync_to_async
def align_user_data(user: User):
    channel_name = get_channel_name(user.profile)

    profile = user.profile

    # match_state = get_event_match_state(profile)

    profile_info = get_profile_info(profile)

    # event_info = get_my_events_info(profile)

    data_obj = AlignUserData(profile_info)

    socket_data = json.dumps(data_obj.__dict__)

    send_data_to_socket_channel(channel_name, SocketActions.ALIGN_USER, socket_data)
