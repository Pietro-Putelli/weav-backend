from django.contrib import admin

from profiles.models import UserProfile, UserFriendRequest, \
    UserFriend


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "id")


@admin.register(UserFriendRequest)
class UserFriendRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "id")


@admin.register(UserFriend)
class UserFriendAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "id")
