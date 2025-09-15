"""
Telegram bot app models for bot user management and conversation tracking.
"""

from django.db import models
from django.contrib.auth.models import User


class TelegramUser(models.Model):
    """
    Telegram user information linked to Django User.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='telegram_user'
    )
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    language_code = models.CharField(max_length=10, default='en')
    
    # Telegram specific fields
    is_bot = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['username']),
        ]
    
    def __str__(self):
        return f"@{self.username}" if self.username else f"Telegram User {self.telegram_id}"


class BotConversation(models.Model):
    """
    Bot conversation state management for handling user interactions.
    """
    CONVERSATION_STATES = [
        ('idle', 'Idle'),
        ('waiting_for_input', 'Waiting for Input'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        TelegramUser, 
        on_delete=models.CASCADE, 
        related_name='conversations'
    )
    state = models.CharField(
        max_length=30, 
        choices=CONVERSATION_STATES, 
        default='idle'
    )
    context = models.JSONField(default=dict, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'state']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.state}"


class BotCommand(models.Model):
    """
    Bot commands configuration and management.
    """
    command = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)
    handler_function = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=True)
    admin_only = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['command']
    
    def __str__(self):
        return f"/{self.command} - {self.description}"


class BotMessage(models.Model):
    """
    Bot message history for analytics and conversation tracking.
    """
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('voice', 'Voice'),
        ('video', 'Video'),
        ('sticker', 'Sticker'),
        ('location', 'Location'),
        ('contact', 'Contact'),
    ]
    
    user = models.ForeignKey(
        TelegramUser, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    message_id = models.BigIntegerField()
    message_type = models.CharField(
        max_length=20, 
        choices=MESSAGE_TYPES, 
        default='text'
    )
    content = models.TextField(blank=True)
    is_bot_message = models.BooleanField(default=False)
    reply_to_message = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['message_type']),
            models.Index(fields=['is_bot_message']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.message_type} - {self.created_at}"


class BotWebhook(models.Model):
    """
    Telegram webhook configuration and status tracking.
    """
    webhook_url = models.URLField()
    is_active = models.BooleanField(default=True)
    secret_token = models.CharField(max_length=100, blank=True)
    last_update_id = models.BigIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Webhook: {self.webhook_url}"


class BotAnalytics(models.Model):
    """
    Bot usage analytics and metrics for monitoring.
    """
    date = models.DateField()
    total_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    messages_received = models.PositiveIntegerField(default=0)
    commands_executed = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.date}"
