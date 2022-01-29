import rest_framework.permissions
from rest_framework.permissions import BasePermission

class IsVerified(BasePermission):
    """
    Allows access only to verified users.
    """
    message = 'verification required'

    def has_permission(self, request, view):
        if request.method in rest_framework.permissions.SAFE_METHODS:
            return bool(request.user)
        return bool(request.user and request.user.is_verified)