from chances.models import UserChance
from chances.serializers import UserChanceSerializer


def create_event_chance(event):
    members = event.members


def get_user_chance(user):
    chance = UserChance.objects.get_chance(user)

    serialized = UserChanceSerializer(chance, context={"user": user})
    return serialized.data


def get_current_chance(user):
    return get_user_chance(user)
