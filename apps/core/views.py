"""
Core app views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user information.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


def health_check(request):
    """
    Basic health check endpoint.
    """
    return Response({
        'status': 'healthy',
        'service': 'noti-api',
        'version': '0.1.0'
    })


def database_health(request):
    """
    Database health check.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        return Response({
            'status': 'healthy',
            'database': 'connected',
            'query_result': result[0] if result else None
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def redis_health(request):
    """
    Redis health check.
    """
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        
        return Response({
            'status': 'healthy',
            'redis': 'connected',
            'test_value': result
        })
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'redis': 'disconnected',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
