from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


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
