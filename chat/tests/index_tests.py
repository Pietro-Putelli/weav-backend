import math
from datetime import datetime
from django.test import TestCase

from chat.models import Chat
from users.models import User

ENTRIES_COUNT = 100


def print_duration(start_date):
    end_date = datetime.now()

    delta = abs(start_date - end_date).total_seconds()
    print(f"END IN = {delta} s")


class ChatTestCase(TestCase):
    def setUp(self):
        users = []

        for i in range(0, ENTRIES_COUNT):
            user = User()
            user.username = str(i)
            user.password = str(i)
            users.append(user)

        User.objects.bulk_create(users)

        chats = []

        for i in range(0, math.floor(ENTRIES_COUNT / 2)):
            chat = Chat(sender=users[i], receiver=users[i + 1])
            chats.append(chat)

        Chat.objects.bulk_create(chats)

