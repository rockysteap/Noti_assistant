"""
Notifications app views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from apps.core.permissions import IsNotificationOwner, CanManageNotifications, IsAdminOrOwner
from apps.core.rate_limiting import NotificationThrottle, APIEndpointThrottle
from .models import (
    Notification, NotificationTemplate, NotificationChannel, 
    NotificationDelivery, NotificationSubscription, NotificationGroup, 
    NotificationSchedule
)
from .serializers import (
    NotificationSerializer, NotificationTemplateSerializer, 
    NotificationChannelSerializer, NotificationDeliverySerializer,
    NotificationSubscriptionSerializer, NotificationGroupSerializer,
    NotificationScheduleSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsNotificationOwner]
    throttle_classes = [NotificationThrottle]
    filterset_fields = ['notification_type', 'priority', 'is_read', 'user']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter notifications to only show user's own notifications.
        """
        if self.request.user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get unread notifications for the current user.
        """
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a notification as read.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read for the current user.
        """
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({'updated': updated})


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification templates.
    """
    queryset = NotificationTemplate.objects.all()
    serializer_class = NotificationTemplateSerializer
    permission_classes = [CanManageNotifications]
    filterset_fields = ['notification_type', 'is_active']
    search_fields = ['name', 'title_template', 'message_template']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active notification templates.
        """
        templates = NotificationTemplate.objects.filter(is_active=True)
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class NotificationChannelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification channels.
    """
    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['channel_type', 'is_active']
    search_fields = ['name']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active notification channels.
        """
        channels = NotificationChannel.objects.filter(is_active=True)
        serializer = self.get_serializer(channels, many=True)
        return Response(serializer.data)


class NotificationDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing notification deliveries.
    """
    queryset = NotificationDelivery.objects.all()
    serializer_class = NotificationDeliverySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'channel', 'notification']
    ordering_fields = ['created_at', 'delivered_at']
    ordering = ['-created_at']


class NotificationSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification subscriptions.
    """
    queryset = NotificationSubscription.objects.all()
    serializer_class = NotificationSubscriptionSerializer
    permission_classes = [IsAdminOrOwner]
    filterset_fields = ['is_enabled', 'channel', 'user']
    ordering = ['user', 'channel']

    def get_queryset(self):
        """
        Filter subscriptions to only show user's own subscriptions.
        """
        if self.request.user.is_staff:
            return NotificationSubscription.objects.all()
        return NotificationSubscription.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current user's notification subscriptions.
        """
        subscriptions = NotificationSubscription.objects.filter(user=request.user)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)


class NotificationGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification groups.
    """
    queryset = NotificationGroup.objects.all()
    serializer_class = NotificationGroupSerializer
    permission_classes = [CanManageNotifications]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['name']


class NotificationScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification schedules.
    """
    queryset = NotificationSchedule.objects.all()
    serializer_class = NotificationScheduleSerializer
    permission_classes = [CanManageNotifications]
    filterset_fields = ['schedule_type', 'is_active']
    search_fields = ['name']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active notification schedules.
        """
        schedules = NotificationSchedule.objects.filter(is_active=True)
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)
