"""
    ASGI or Asynchronous Server Gateway Interface, is the successor of WSGI.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from core.middleware import ChatMiddleware
from websocket.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "real.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": ChatMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
