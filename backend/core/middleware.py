from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework.authtoken.models import Token

from business.models import BusinessToken


@database_sync_to_async
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


@database_sync_to_async
def get_business(token_key):
    try:
        business = BusinessToken.objects.get(key=token_key).business
        return business
    except BusinessToken.DoesNotExist:
        return None


class WebsocketMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        is_business = False
        try:
            params = dict(
                (x.split("=") for x in scope["query_string"].decode().split("&"))
            )
            token_key = params.get("token", None)

            is_business = "business" in scope.get("path")
        except ValueError:
            token_key = None

        scope["user"] = None
        scope["business"] = None

        if is_business:
            scope["business"] = await get_business(token_key)
        else:
            scope["user"] = await get_user(token_key)

        return await super().__call__(scope, receive, send)
