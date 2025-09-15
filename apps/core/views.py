"""
Core app views.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connection
from django.contrib.auth.models import User
from .models import UserProfile, SystemSettings, AuditLog
from .serializers import UserSerializer, UserProfileSerializer, SystemSettingsSerializer, AuditLogSerializer
from .permissions import IsOwnerOrReadOnly, IsAdminOrOwner, IsSystemAdmin


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminOrOwner]

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """
        Get or update current user's profile.
        """
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        if request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing system settings.
    """
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [IsSystemAdmin]

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active system settings.
        """
        settings = SystemSettings.objects.filter(is_active=True)
        serializer = self.get_serializer(settings, many=True)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsSystemAdmin]
    filterset_fields = ['action', 'resource', 'user']
    search_fields = ['action', 'resource', 'details']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


def health_check(request):
    """
    Basic health check endpoint.
    """
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'healthy',
        'service': 'noti-api',
        'version': '0.1.0'
    })


def database_health(request):
    """
    Database health check.
    """
    from django.http import JsonResponse
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'query_result': result[0] if result else None
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=503)


def redis_health(request):
    """
    Redis health check.
    """
    from django.http import JsonResponse
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'redis': 'connected',
            'test_value': result
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'redis': 'disconnected',
            'error': str(e)
        }, status=503)
