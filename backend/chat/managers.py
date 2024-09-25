from operator import is_
from django.db.models import Manager
from django.db.models.query_utils import Q
from profiles.models import UserFriend


class MessageManager(Manager):
    def create(self, **kwargs):
        chat = kwargs.pop("chat")
        chat.update_date()
        return super().create(chat=chat, **kwargs)


class ChatMessageManager(MessageManager):
    def get_messages(self, chat_id, profile):
        return (
            self.get_queryset()
            .filter(chat__id=chat_id)
            .filter(
                Q(is_anonymous=False) | Q(Q(is_anonymous=True) & Q(receiver=profile))
            )
        )

    def get_or_none(self, msg_id):
        queryset = self.get_queryset().filter(is_anonymous=False, id=msg_id)

        if queryset.exists():
            return queryset.first()
        return None

    def create(self, **kwargs):
        chat = kwargs.get("chat")
        sender = kwargs.get("sender")

        if not chat.is_active:
            chat_sender = chat.sender

            if chat_sender != sender:
                chat.activate()

        queryset = self.get_queryset().filter(chat=chat)

        chat_sender = chat.sender.id

        receiver = kwargs.get("receiver")
        message_receiver = receiver.id

        if chat.is_anonymous:
            if chat_sender == message_receiver:
                chat.set_anonymous(False)

                queryset.update(is_anonymous=False)
                kwargs["is_anonymous"] = False
        else:
            kwargs["is_anonymous"] = False

        return super().create(**kwargs)


class ChatManager(Manager):
    def _get_chats(self, profile):
        queryset = self.get_queryset()
        blocked_users = profile.blocked_users.all()

        from .models import ChatMessage

        queryset = queryset.filter(
            (Q(sender=profile) | Q(receiver=profile))
            & Q(~Q(sender__in=blocked_users) & ~Q(receiver__in=blocked_users))
        )

        chats = []

        for chat in queryset:
            messages = ChatMessage.objects.get_messages(chat.id, profile)

            if messages.exists():
                chats.append(chat)

        return chats

    def create(self, **kwargs):
        sender = kwargs.get("sender")
        receiver = kwargs.get("receiver")

        are_friends = UserFriend.objects.are_friends(sender, receiver)

        return super().create(is_active=are_friends, **kwargs)

    def get_my_chats(self, user):
        return self._get_chats(user)

    def get_chat(self, user, receiver):
        chats = self.get_queryset().filter(
            Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user)
        )
        if chats.exists():
            return chats.first()
        return None

    def get_or_create(self, sender, receiver):
        chat = self.get_chat(sender, receiver)

        if chat is None:
            chat = self.create(sender=sender, receiver=receiver)

        return chat

    def get_recent(self, user):
        chats = self.get_my_chats(user)
        ord_chats = sorted(chats, key=lambda x: x.updated_at, reverse=True)
        return ord_chats

    # Remove chat when user block another user
    def remove_blocked(self, *args):
        chats = self.get_chat(*args)

        if chats is not None:
            chats.delete()


class BusinessChatMessageManager(MessageManager):
    def get_or_none(self, msg_id):
        queryset = self.get_queryset().filter(id=msg_id)
        if queryset.exists():
            return queryset.first()
        return None


class BusinessChatManager(Manager):
    def get_for_id(self, id, user):
        return self.get_queryset().filter(business__id=id, profile__user=user)
