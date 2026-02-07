"""
Custom permissions for the API.
"""
from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows access only to object owners or admins.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        # Check for user attribute on the object
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object is the user itself
        return obj == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read-only access to all, but write access only to admins.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
