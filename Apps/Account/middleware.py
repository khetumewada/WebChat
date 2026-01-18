from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from django.utils.functional import SimpleLazyObject

class JWTAutoRefreshTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        access_token = request.COOKIES.get("access")
        refresh_token = request.COOKIES.get("refresh")

        # No access token → public request
        if not access_token:
            return None

        # Check access token validity
        try:
            AccessToken(access_token)
            return None  # token valid → continue request

        except TokenError:
            # Access token expired or invalid
            pass

        # Access expired but refresh missing → logout
        if not refresh_token:
            return self.logout_response("Access token expired")

        # Try refreshing token
        try:
            serializer = TokenRefreshSerializer(
                data={"refresh": refresh_token}
            )
            serializer.is_valid(raise_exception=True)

            new_access = serializer.validated_data["access"]
            new_refresh = serializer.validated_data.get("refresh")

            # Attach to request for process_response
            request.new_access_token = new_access
            request.new_refresh_token = new_refresh

            # Manually authenticate user
            user = JWTAuthentication().get_user(AccessToken(new_access))
            request.user = user

        except (InvalidToken, TokenError, User.DoesNotExist):
            return self.logout_response("Invalid refresh token")

        except TokenError:
            return self.logout_response("Refresh token expired")

        return None

    def process_response(self, request, response):
        if hasattr(request, "new_access_token"):
            response.set_cookie(
                "access",
                request.new_access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )

        if hasattr(request, "new_refresh_token") and request.new_refresh_token:
            response.set_cookie(
                "refresh",
                request.new_refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )

        return response

    def logout_response(self, message):
        response = JsonResponse({"detail": message}, status=401)
        response.delete_cookie("access", samesite="Lax")
        response.delete_cookie("refresh", samesite="Lax")
        return response


User = get_user_model()

def get_jwt_user(request):
    access = request.COOKIES.get("access")
    if not access:
        return AnonymousUser()
    try:
        token = AccessToken(access)
        return User.objects.get(id=token["user_id"])
    except Exception:
        return AnonymousUser()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Database query only happens if request.user is actually accessed
        request.user = SimpleLazyObject(lambda: get_jwt_user(request))
