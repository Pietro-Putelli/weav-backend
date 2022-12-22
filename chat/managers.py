from django.db.models import Manager
from django.db.models.query_utils import Q
from django.db.models import OuterRef, Subquery
from django.db.models.expressions import F

from chances.models import UserChance
from profiles.models import UserFriend


class MessageManager(Manager):
    def create(self, **kwargs):
        chat = kwargs.pop("chat")
        chat.update_date()
        return super().create(chat=chat, **kwargs)


class ChatMessageManager(MessageManager):
    def get_all(self, chat, user):
        query = Q(chat=chat)

        if user == chat.sender and chat.sender_deleted_to is not None:
            query &= Q(id__gt=chat.sender_deleted_to.id)

        if user == chat.receiver and chat.receiver_deleted_to is not None:
            query &= Q(id__gt=chat.receiver_deleted_to.id)

        return self.get_queryset().filter(query)

    def get_last_10_messages(self, chat_id):
        return self.get_queryset().filter(chat__id=chat_id)[:10]

    def get_or_none(self, msg_id):
        queryset = self.get_queryset().filter(id=msg_id)
        if queryset.exists():
            return queryset.first()
        return None

    def create(self, **kwargs):
        chat = kwargs.get("chat")
        message_sender = kwargs.get("sender")

        if not chat.is_active:
            chat_sender = chat.sender

            if chat_sender != message_sender:
                chat.activate()

        return super().create(**kwargs)


class ChatManager(Manager):
    def _get_chats(self, user):
        queryset = self.get_queryset()
        blocked_users = user.profile.blocked_users.all()

        return queryset.filter(
            (Q(sender=user) | Q(receiver=user))
            & Q(~Q(sender__in=blocked_users) & ~Q(receiver__in=blocked_users))
        )

    def create(self, **kwargs):
        sender = kwargs.get("sender")
        receiver = kwargs.get("receiver")

        are_friends = UserFriend.objects.are_friends(sender, receiver)

        UserChance.objects.get_chances(sender).delete()

        return super().create(is_active=are_friends, **kwargs)

    def get_my_chats(self, user):
        from chat.models import ChatMessage

        subquery = ChatMessage.objects.filter(chat=OuterRef("pk"))

        return self._get_chats(user).annotate(
            last_message=Subquery(subquery.values("id")[:1])).filter(
            Q(Q(sender=user) & ~Q(sender_deleted_to=F("last_message"))) | Q(
                Q(receiver=user) & ~Q(receiver_deleted_to=F("last_message"))))

    def get_chat(self, user, receiver):
        chats = self.get_queryset().filter(
            Q(sender=user, receiver=receiver) | Q(
                sender=receiver, receiver=user)
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
        return self.get_my_chats(user).order_by("-updated_at")

    # Remove chat when user block another user
    def remove_blocked(self, *args):
        self.get_chat(*args).delete()


class BusinessChatMessageManager(MessageManager):
    def get_or_none(self, msg_id):
        queryset = self.get_queryset().filter(id=msg_id)
        if queryset.exists():
            return queryset.first()
        return None


class BusinessChatManager(Manager):
    def get_for_id(self, id, user):
        return self.get_queryset().filter(business__id=id, profile__user=user)
