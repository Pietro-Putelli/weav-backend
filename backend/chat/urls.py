from django.urls import path

from chat.views import (ChatView, get_chat_by_user, get_chat_for_business,
                        mute_chat, read_business_chat_messages, read_messages,
                        search_chats, ShareViewSet, get_my_business_chats,
                        create_business_chat, MessagesViewSet)

urlpatterns = [
    path("", ChatView.as_view()),

    path("messages/user/", MessagesViewSet.as_view({"get": "user_messages"})),
    path("messages/business/", MessagesViewSet.as_view({"get": "business_messages"})),

    path("user/", get_chat_by_user),
    path("read/", read_messages),
    path("mute/", mute_chat),
    path("search/", search_chats),

    path("share/moment/", ShareViewSet.as_view({"post": "moment"})),
    path("share/profile/", ShareViewSet.as_view({"post": "profile"})),
    path("share/reaction/", ShareViewSet.as_view({"post": "reaction"})),

    # USER-TO-BUSINESS
    path("business/create/", create_business_chat),
    path("business/get/", get_my_business_chats),
    path("business/id/", get_chat_for_business),
    path("business/read/", read_business_chat_messages),
]
