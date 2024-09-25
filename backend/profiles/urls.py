from django.urls.conf import path

from profiles.views import (
    ProfileAPIView,
    ProfileSettings,
    BlockUser,
    change_profile_picture,
    search_users,
    UserFeedAPIView,
    UserFriendRequestAPIView,
    UserFriendAPIView,
    get_recent_users,
    update_profile_language,
)

urlpatterns = [
    path("", ProfileAPIView.as_view(), name="user_profile"),
    path("update/language/", update_profile_language, name="update_profile_language"),
    path("update/picture/", change_profile_picture, name="change_profile_picture"),
    path("settings/", ProfileSettings.as_view(), name="profile_settings"),
    path("block/", BlockUser.as_view(), name="block_user"),
    path("search/", search_users, name="search_users"),
    path("recent/", get_recent_users, name="recent_users"),
    path("feeds/", UserFeedAPIView.as_view(), name="user_feeds"),
    path("friend/request/", UserFriendRequestAPIView.as_view(), name="friend_request"),
    path("friend/", UserFriendAPIView.as_view(), name="friend"),
]
