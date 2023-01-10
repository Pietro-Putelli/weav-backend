from django.urls.conf import path

from moments.views import EventMomentAPIView, UserMomentAPIView, get_event_moments, \
    get_user_moments, CurrentEventMomentAPIView, get_tagged_user_moments, \
    get_archived_event_moments, get_event_moment_participants, \
    get_event_moment_detail, get_my_events, get_user_moments_by_id, \
    user_go_to_event


def event_path(endpoint, view, **kwargs):
    return path("event/" + endpoint, view, **kwargs)


urlpatterns = [
    path("user/", UserMomentAPIView.as_view(), name="user"),
    path("user/get/", get_user_moments, name="get_user_moments"),
    path("user/get/id/", get_user_moments_by_id, name="get_user_moments_by_id"),

    event_path("", EventMomentAPIView.as_view(), name="event"),
    event_path("get/", get_event_moments, name="get_event_moments"),
    event_path("current/", CurrentEventMomentAPIView.as_view(), name="current_event_moment"),
    event_path("detail/", get_event_moment_detail, name="event_moment_detail"),
    event_path("going/", user_go_to_event, name="add_user_to_event"),
    event_path("mine/", get_my_events, name="get_my_events"),

    event_path("tagged/", get_tagged_user_moments, name="get_tagged_user_moments"),
    event_path("archived/", get_archived_event_moments, name="get_archived_event_moments"),

    event_path("participants/", get_event_moment_participants, name="event_participants")
]
