from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Restricts access to accounts whose Role is 'admin' (case-insensitive).

    Requires CustomJWTAuthentication (accounts/authentication.py) to run
    first, so request.user is a real accounts.models.User instance with
    a resolvable .role FK — plain JWTAuthentication won't do, since it
    resolves against Django's built-in auth.User model instead.

    There's no seeded Role data to confirm the exact name against, and
    RegisterSerializer hardcodes role_id=2 for self-signup — so this
    checks role_name == 'admin' rather than a guessed numeric id. If
    your actual admin role is named differently, update ADMIN_ROLE_NAME.
    """

    message = "Admin access required."

    ADMIN_ROLE_NAME = 'admin'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return False
        role = getattr(user, 'role', None)
        return bool(role and role.role_name.lower() == self.ADMIN_ROLE_NAME)
