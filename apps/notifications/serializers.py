"""
Notifications app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from apps.core.validators import (
    NotificationTypeValidator, PriorityValidator, ChannelTypeValidator,
    CronExpressionValidator, FutureDateTimeValidator, CustomValidationMixin
)
from .models import (
    Notification, NotificationTemplate, NotificationChannel, 
    NotificationDelivery, NotificationSubscription, NotificationGroup, 
    NotificationSchedule
)


class NotificationTemplateSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for NotificationTemplate model with enhanced validation.
    """
    notification_type = serializers.CharField(validators=[NotificationTypeValidator()])
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'title_template', 'message_template', 
            'notification_type', 'is_active', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'name': {'max_length': 100},
            'title_template': {'max_length': 200},
            'message_template': {'max_length': 1000},
        }
    
    def validate_name(self, value):
        """Validate template name uniqueness."""
        if self.instance and self.instance.name == value:
            return value
        
        if NotificationTemplate.objects.filter(name=value).exists():
            raise serializers.ValidationError("A template with this name already exists.")
        
        return value
    
    def validate_title_template(self, value):
        """Validate title template contains required variables."""
        if '{title}' not in value:
            raise serializers.ValidationError("Title template must contain {title} variable.")
        return value
    
    def validate_message_template(self, value):
        """Validate message template contains required variables."""
        if '{message}' not in value:
            raise serializers.ValidationError("Message template must contain {message} variable.")
        return value


class NotificationChannelSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for NotificationChannel model with enhanced validation.
    """
    channel_type = serializers.CharField(validators=[ChannelTypeValidator()])
    config = serializers.CharField(validators=[CustomValidationMixin.validate_config])
    
    class Meta:
        model = NotificationChannel
        fields = [
            'id', 'name', 'channel_type', 'is_active', 'config',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'name': {'max_length': 100},
        }
    
    def validate_name(self, value):
        """Validate channel name uniqueness."""
        if self.instance and self.instance.name == value:
            return value
        
        if NotificationChannel.objects.filter(name=value).exists():
            raise serializers.ValidationError("A channel with this name already exists.")
        
        return value


class NotificationSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for Notification model with enhanced validation.
    """
    user = serializers.StringRelatedField(read_only=True)
    template = NotificationTemplateSerializer(read_only=True)
    notification_type = serializers.CharField(validators=[NotificationTypeValidator()])
    priority = serializers.CharField(validators=[PriorityValidator()])
    scheduled_at = serializers.DateTimeField(validators=[FutureDateTimeValidator()], required=False)
    expires_at = serializers.DateTimeField(validators=[FutureDateTimeValidator()], required=False)
    metadata = serializers.CharField(validators=[CustomValidationMixin.validate_metadata], required=False)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'template', 'title', 'message', 'notification_type',
            'priority', 'is_read', 'scheduled_at', 'expires_at', 'metadata',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'title': {'max_length': 200},
            'message': {'max_length': 1000},
        }
    
    def validate_title(self, value):
        """Validate title is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message is not empty."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value.strip()
    
    def validate(self, data):
        """Validate notification data."""
        scheduled_at = data.get('scheduled_at')
        expires_at = data.get('expires_at')
        
        if scheduled_at and expires_at and scheduled_at >= expires_at:
            raise serializers.ValidationError("Scheduled time must be before expiration time.")
        
        return data


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


class NotificationScheduleSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for NotificationSchedule model with enhanced validation.
    """
    template = NotificationTemplateSerializer(read_only=True)
    cron_expression = serializers.CharField(validators=[CronExpressionValidator()])
    
    class Meta:
        model = NotificationSchedule
        fields = [
            'id', 'name', 'template', 'schedule_type', 'cron_expression',
            'is_active', 'last_run', 'next_run', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'name': {'max_length': 100},
        }
    
    def validate_name(self, value):
        """Validate schedule name uniqueness."""
        if self.instance and self.instance.name == value:
            return value
        
        if NotificationSchedule.objects.filter(name=value).exists():
            raise serializers.ValidationError("A schedule with this name already exists.")
        
        return value
