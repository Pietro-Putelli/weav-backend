from django.urls import path

from websocket.consumers import UserChatConsumer, BusinessChatConsumer

websocket_urlpatterns = [
    # USER < > USER or DISCUSSIONS
    path("ws/chat/user/", UserChatConsumer.as_asgi()),

    # USER < > BUSINESS
    path("ws/chat/business/", BusinessChatConsumer.as_asgi()),
]
