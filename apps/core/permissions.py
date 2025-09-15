"""
Custom permission classes for the Noti project.
"""

from rest_framework import permissions
from django.contrib.auth.models import User


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.user == request.user


class IsTelegramUser(permissions.BasePermission):
    """
    Permission to only allow Telegram users.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has a Telegram user profile
        return hasattr(request.user, 'telegram_user')


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission to allow admin users or object owners.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user is the owner of the object
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For objects without a user field, check other ownership patterns
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsNotificationOwner(permissions.BasePermission):
    """
    Permission to only allow users to access their own notifications.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Users can only access their own notifications
        return obj.user == request.user


class IsTelegramBotOwner(permissions.BasePermission):
    """
    Permission to only allow users to access their own Telegram bot data.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if the object belongs to the user's Telegram profile
        if hasattr(obj, 'user'):
            return obj.user == request.user.telegram_user
        
        return False


class CanManageNotifications(permissions.BasePermission):
    """
    Permission to manage notifications (create, send, etc.).
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admin users can manage all notifications
        if request.user.is_staff:
            return True
        
        # Regular users can manage their own notifications
        return True
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Users can only manage their own notifications
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsSystemAdmin(permissions.BasePermission):
    """
    Permission to only allow system administrators.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff and
            request.user.is_superuser
        )
