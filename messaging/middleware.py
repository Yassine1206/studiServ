# messaging/middleware.py
"""JWT authentication middleware for Django Channels WebSockets.

Reads the JWT access token from the `?token=...` query string when opening
a WebSocket, validates it via simplejwt, and attaches the matching User
to `scope['user']`.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model


@database_sync_to_async
def _get_user(user_id):
    User = get_user_model()
    try:
        return User.objects.get(pk=int(user_id))
    except (User.DoesNotExist, TypeError, ValueError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token")

        if token_list:
            token = token_list[0]
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                validated = AccessToken(token)  # raises on invalid/expired
                user_id = validated.get("user_id")
                if user_id is not None:
                    scope["user"] = await _get_user(user_id)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    "WS JWT auth failed: %s", e
                )

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
