"""
    ASGI or Asynchronous Server Gateway Interface, is the successor of WSGI.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from core.middleware import WebsocketMiddleware
from websocket.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": WebsocketMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
