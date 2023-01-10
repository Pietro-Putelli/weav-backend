from django.urls.conf import path

from profiles.views import (
    ProfileAPIView,
    ProfileSettings,
    BlockUser,
    change_profile_picture,
    update_user_password, search_users, UserFeedAPIView, UserFriendRequestAPIView,
    UserFriendAPIView, get_profile_info, get_user_interests_list, get_recent_users
)

urlpatterns = [
    path("", ProfileAPIView.as_view(), name="user_profile"),
    path("info/", get_profile_info, name="profile_info"),

    path("update/password/", update_user_password, name="update_user_password"),
    path("update/picture/", change_profile_picture, name="change_profile_picture"),

    path("settings/", ProfileSettings.as_view(), name="profile_settings"),

    path("block/", BlockUser.as_view(), name="block_user"),
    path("search/", search_users, name="search_users"),
    path("recent/", get_recent_users, name="recent_users"),
    path("feeds/", UserFeedAPIView.as_view(), name="user_feeds"),

    path("friend/request/", UserFriendRequestAPIView.as_view(), name="friend_request"),
    path("friend/", UserFriendAPIView.as_view(), name="friend"),

    path("interests/list/", get_user_interests_list, name="interests_list")
]
