# messaging/middleware.py
"""JWT authentication middleware for Django Channels WebSockets.

The SPA passes the JWT access token as a `?token=...` query string parameter
when opening a WebSocket. This middleware decodes the token, fetches the
corresponding User, and attaches it to `scope['user']` so consumers see an
authenticated user instead of AnonymousUser.
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
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token")
        scope["user"] = AnonymousUser()

        if token_list:
            token = token_list[0]
            try:
                from rest_framework_simplejwt.tokens import UntypedToken
                from rest_framework_simplejwt.exceptions import TokenError
                try:
                    UntypedToken(token)  # raises if invalid
                    import jwt as pyjwt
                    from django.conf import settings
                    secret = getattr(settings, "SIMPLE_JWT", {}).get(
                        "SIGNING_KEY", settings.SECRET_KEY
                    )
                    decoded = pyjwt.decode(token, secret, algorithms=["HS256"])
                    user_id = decoded.get("user_id")
                    if user_id is not None:
                        scope["user"] = await _get_user(user_id)
                except (TokenError, Exception):
                    pass
            except ImportError:
                pass

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
