from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()

        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode()

        cookies = {}
        for item in cookie_header.split(";"):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                cookies[k] = v

        token = cookies.get("access")

        if token:
            try:
                access = AccessToken(token)
                scope["user"] = await self.get_user(access["user_id"])
            except Exception:
                pass

        return await self.inner(scope, receive, send)

    async def get_user(self, user_id):
        return await database_sync_to_async(User.objects.get)(id=user_id)