from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


ADMIN_ROLE_ID = 1


class IsAdminRole(BasePermission):
    """
    Only allows requests carrying a valid JWT whose `role_id` claim is
    ADMIN_ROLE_ID.

    This project issues JWTs by hand in accounts/views.py:LoginView
    (`RefreshToken()` with custom claims: user_id, email, role_id,
    full_name) instead of going through Django's normal auth-user
    machinery, so `request.user` isn't reliably populated by
    JWTAuthentication. We read `role_id` straight off the token instead,
    the same place LoginView put it.
    """

    message = "Admin access required."

    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return False

        raw_token = auth_header.split(' ', 1)[1].strip()
        try:
            token = AccessToken(raw_token)
        except (TokenError, InvalidToken):
            return False

       
        request.jwt_payload = token
        return token.get('role_id') == ADMIN_ROLE_ID
