from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    "

    message = "Admin access required."

    ADMIN_ROLE_NAME = 'admin'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return False
        role = getattr(user, 'role', None)
        return bool(role and role.role_name.lower() == self.ADMIN_ROLE_NAME)
