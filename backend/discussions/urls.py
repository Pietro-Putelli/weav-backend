from django.urls import path

from discussions.views import mute_discussion, delete_discussion, get_messages

urlpatterns = [
    path("mute/", mute_discussion, name="mute_discussion"),
    path("delete/", delete_discussion, name="delete_discussion"),
    path("messages/", get_messages, name="get_messages")
]
