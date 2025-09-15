"""
Notifications app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Notification, NotificationTemplate, NotificationChannel, 
    NotificationDelivery, NotificationSubscription, NotificationGroup, 
    NotificationSchedule
)


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationTemplate model.
    """
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'title_template', 'message_template', 
            'notification_type', 'is_active', 'created_at', 'updated_at'
        ]


class NotificationChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationChannel model.
    """
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'is_active', 'config',
            'created_at', 'updated_at'
        ]


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    user = serializers.StringRelatedField(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'template', 'title', 'message', 'notification_type',
            'priority', 'is_read', 'scheduled_at', 'expires_at', 'metadata',
            'created_at', 'updated_at'
        ]


class NotificationDeliverySerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationDelivery model.
    """
    notification = NotificationSerializer(read_only=True)
    channel = NotificationChannelSerializer(read_only=True)
    
    class Meta:
        model = NotificationDelivery
        fields = [
            'id', 'notification', 'channel', 'status', 'external_id',
            'error_message', 'delivered_at', 'created_at', 'updated_at'
        ]


class NotificationSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationSubscription model.
    """
    user = serializers.StringRelatedField(read_only=True)
    channel = NotificationChannelSerializer(read_only=True)
    
    class Meta:
        model = NotificationSubscription
        fields = [
            'id', 'user', 'channel', 'notification_types', 'is_enabled',
            'created_at', 'updated_at'
        ]


class NotificationGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationGroup model.
    """
    users = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = NotificationGroup
        fields = [
            'id', 'name', 'description', 'users', 'is_active',
            'created_at', 'updated_at'
        ]


class NotificationScheduleSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationSchedule model.
    """
    template = NotificationTemplateSerializer(read_only=True)
    
    class Meta:
        model = NotificationSchedule
        fields = [
            'id', 'name', 'template', 'schedule_type', 'cron_expression',
            'is_active', 'last_run', 'next_run', 'created_at', 'updated_at'
        ]
