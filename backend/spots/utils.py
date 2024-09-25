from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from devices.models import Device
from devices.utils import NotificationType
from .models import Spot


def send_spot_reply_notification(my_profile, spot):
    replies_count = spot.replies.count()

    recevier = spot.profile.user

    data = {"id": spot.uuid}

    socket_channel = f"user.{recevier.uuid}"

    send_data_to_socket_channel(socket_channel, SocketActions.USER_SPOT_REPLIES, data)

    device = Device.objects.filter(user=recevier).first()

    if device and not device.is_business:
        device.send_notification(NotificationType.SPOT_REPLY, my_profile, spot)
