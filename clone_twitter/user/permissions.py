from rest_framework.permissions import BasePermission

class IsVerified(BasePermission):
    """
    Allows access only to verified users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_verified)