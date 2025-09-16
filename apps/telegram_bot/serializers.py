"""
Telegram bot app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from apps.core.validators import (
    TelegramUsernameValidator, URLValidator, CustomValidationMixin
)
from .models import (
    TelegramUser, BotConversation, BotCommand, BotMessage, 
    BotWebhook, BotAnalytics
)


class TelegramUserSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for TelegramUser model with enhanced validation.
    """
    user = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(
        required=False, 
        allow_blank=True, 
        validators=[TelegramUsernameValidator()]
    )
    language_code = serializers.CharField(
        required=False, 
        allow_blank=True, 
        max_length=10
    )
    
    class Meta:
        model = TelegramUser
        fields = [
            'id', 'user', 'telegram_id', 'username', 'first_name', 'last_name',
            'language_code', 'is_bot', 'is_premium', 'is_verified', 
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'first_name': {'max_length': 100},
            'last_name': {'max_length': 100},
        }
    
    def validate_telegram_id(self, value):
        """Validate telegram_id uniqueness."""
        if self.instance and self.instance.telegram_id == value:
            return value
        
        if TelegramUser.objects.filter(telegram_id=value).exists():
            raise serializers.ValidationError("A user with this Telegram ID already exists.")
        
        return value


class BotConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for BotConversation model.
    """
    user = TelegramUserSerializer(read_only=True)
    
    class Meta:
        model = BotConversation
        fields = [
            'id', 'user', 'state', 'context', 'last_activity', 'created_at'
        ]


class BotCommandSerializer(serializers.ModelSerializer):
    """
    Serializer for BotCommand model.
    """
    
    class Meta:
        model = BotCommand
        fields = [
            'id', 'command', 'description', 'handler_function', 'is_active',
            'requires_auth', 'admin_only', 'created_at', 'updated_at'
        ]


class BotMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for BotMessage model.
    """
    user = TelegramUserSerializer(read_only=True)
    reply_to_message = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = BotMessage
        fields = [
            'id', 'user', 'message_id', 'message_type', 'content',
            'is_bot_message', 'reply_to_message', 'created_at'
        ]


class BotWebhookSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for BotWebhook model with enhanced validation.
    """
    webhook_url = serializers.URLField(validators=[URLValidator()])
    
    class Meta:
        model = BotWebhook
        fields = [
            'id', 'webhook_url', 'is_active', 'secret_token',
            'last_update_id', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'secret_token': {'max_length': 100},
        }
    
    def validate_webhook_url(self, value):
        """Validate webhook URL format."""
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("Webhook URL must start with http:// or https://")
        return value


class BotAnalyticsSerializer(serializers.ModelSerializer):
    """
    Serializer for BotAnalytics model.
    """
    
    class Meta:
        model = BotAnalytics
        fields = [
            'id', 'date', 'total_users', 'active_users', 'messages_sent',
            'messages_received', 'commands_executed', 'errors_count', 'created_at'
        ]
