"""
Telegram bot app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    TelegramUser, BotConversation, BotCommand, BotMessage, 
    BotWebhook, BotAnalytics
)


class TelegramUserSerializer(serializers.ModelSerializer):
    """
    Serializer for TelegramUser model.
    """
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = TelegramUser
        fields = [
            'id', 'user', 'telegram_id', 'username', 'first_name', 'last_name',
            'language_code', 'is_bot', 'is_premium', 'is_verified', 
            'created_at', 'updated_at'
        ]


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


class BotWebhookSerializer(serializers.ModelSerializer):
    """
    Serializer for BotWebhook model.
    """
    
    class Meta:
        model = BotWebhook
        fields = [
            'id', 'webhook_url', 'is_active', 'secret_token',
            'last_update_id', 'created_at', 'updated_at'
        ]


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
