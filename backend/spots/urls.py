from django.urls import path

from spots.views import SpotsAPIView, reply_spot, get_my_spots, get_spot_replies

urlpatterns = [
    path("", SpotsAPIView.as_view(), name="spots"),
    path("reply/", reply_spot, name="reply"),
    path("mine/", get_my_spots, name="my_spots"),
    path("replies/", get_spot_replies, name="spot_replies"),
]
