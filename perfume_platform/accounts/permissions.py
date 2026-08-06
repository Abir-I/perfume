"""
Shared DRF permission classes for accounts.User (our custom user table,
not Django's built-in auth.User — see accounts/authentication.py).
"""

from rest_framework.permissions import BasePermission

ADMIN_ROLE_ID = 1  # matches the 'admin' row seeded in the `role` table


class IsAdminRole(BasePermission):
    """
    Only allows access to logged-in users whose role_id is the admin role.
    Must be combined with IsAuthenticated + CustomJWTAuthentication on the
    view, since this permission assumes request.user is already resolved
    against accounts.models.User.
    """

    message = "You must be an administrator to perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and getattr(user, 'is_authenticated', False)
            and getattr(user, 'role_id', None) == ADMIN_ROLE_ID
        )
