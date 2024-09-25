from django.urls import path
from websocket.consumers import UserChatConsumer, BusinessChatConsumer

websocket_urlpatterns = [
    path("ws/user/", UserChatConsumer.as_asgi()),
    path("ws/business/", BusinessChatConsumer.as_asgi()),
]
