from django.contrib import admin

from profiles.models import UserProfile, UserFriendRequest, \
    UserFriend, BusinessProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "id")


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "id", "accepted_terms")

    @admin.display(
        boolean=True,
        description='accepted_terms',
    )
    def accepted_terms(self, profile):
        return profile.accepted_terms


@admin.register(UserFriendRequest)
class UserFriendRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "id")


@admin.register(UserFriend)
class UserFriendAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "id")
