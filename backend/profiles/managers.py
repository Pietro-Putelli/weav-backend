from django.db import models
from django.db.models.query_utils import Q


class FriendManager(models.Manager):
    def _get_friend_queryset(self, user, friend):
        return self.get_queryset().filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user))

    def remove_blocked(self, *args):
        self._get_friend_queryset(*args).delete()


class UserFriendManager(FriendManager):
    def are_friends(self, *args):
        return self._get_friend_queryset(*args).exists()

    def delete_if_friends(self, *args):
        queryset = self._get_friend_queryset(*args)

        if queryset.exists():
            queryset.delete()

            return True
        return False

    def get_friends(self, user):
        friends = self.get_queryset().filter(Q(user=user) | Q(friend=user)).order_by("-created_at")
        count = friends.count()

        users = []

        for friend in friends:
            if user.id == friend.friend.id:
                users.append(friend.user)
            else:
                users.append(friend.friend)

        return users, count

    def get_friends_in(self, user, users):
        friends = self.get_queryset().filter(
            Q(Q(user=user) & Q(friend__in=users)) | Q(Q(friend=user) & Q(user__in=users)))

        count = friends.count()

        users = []

        for friend in friends:
            if user.id == friend.friend.id:
                users.append(friend.user)
            else:
                users.append(friend.friend)

        return users, count


class UserFriendRequestManager(FriendManager):
    def get_requests_for(self, user):
        return self.get_queryset().filter(friend=user).order_by("-created_at")
