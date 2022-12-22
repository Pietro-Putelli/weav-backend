from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from moments.models import UserMoment
from websocket.actions import SocketActions
from websocket.utils import send_data_to_socket_channel
from django.db.models.signals import m2m_changed


@receiver(post_delete, sender=UserMoment)
def post_delete_user_moment(sender, instance, **kwargs):
    if instance.location:
        instance.location.delete()


'''
    Send websocket message when new moment is created and user is mentioned
'''


def post_save_send_moment_mention(sender, instance, **kwargs):
    mentioned_users = instance.users_tag.all()

    if mentioned_users.count() > 0:
        for user in mentioned_users:
            socket_channel = f"user.{user.id}"
            send_data_to_socket_channel(socket_channel, SocketActions.USER_MENTION_MOMENT, None)


m2m_changed.connect(post_save_send_moment_mention, sender=UserMoment.users_tag.through)
