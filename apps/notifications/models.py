"""
Notifications app models for multi-channel notification system.
"""

# pylint: disable=import-error
from django.db import models
from django.contrib.auth.models import User


class NotificationTemplate(models.Model):
    """
    Notification templates for reusable message formats.
    """
    name = models.CharField(max_length=100, unique=True)
    title_template = models.CharField(max_length=200)
    message_template = models.TextField()
    notification_type = models.CharField(
        max_length=20, 
        choices=[
            ('info', 'Information'),
            ('warning', 'Warning'),
            ('error', 'Error'),
            ('success', 'Success'),
        ], 
        default='info'
    )
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"Template: {self.name}"


class NotificationChannel(models.Model):
    """
    Notification delivery channels configuration.
    """
    CHANNEL_TYPES = [
        ('email', 'Email'),
        ('telegram', 'Telegram'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('webhook', 'Webhook'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.channel_type})"


class Notification(models.Model):
    """
    Enhanced notification model with multi-channel delivery support.
    """
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
        ('urgent', 'Urgent'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    template = models.ForeignKey(
        NotificationTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='info'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_LEVELS, 
        default='normal'
    )
    is_read = models.BooleanField(default=False)
    
    # Scheduling and expiration
    scheduled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class NotificationDelivery(models.Model):
    """
    Track notification delivery across different channels.
    """
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='deliveries'
    )
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, 
        choices=DELIVERY_STATUS, 
        default='pending'
    )
    external_id = models.CharField(max_length=100, blank=True)  # External service ID
    error_message = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['notification', 'channel']
        indexes = [
            models.Index(fields=['notification', 'status']),
            models.Index(fields=['channel', 'status']),
        ]
    
    def __str__(self):
        return f"{self.notification.title} via {self.channel.name} - {self.status}"


class NotificationSubscription(models.Model):
    """
    User notification preferences and channel subscriptions.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_subscriptions'
    )
    channel = models.ForeignKey(NotificationChannel, on_delete=models.CASCADE)
    notification_types = models.JSONField(
        default=list, 
        blank=True
    )  # List of notification types user wants
    is_enabled = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user', 'channel']
        unique_together = ['user', 'channel']
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.channel.name}"


class NotificationGroup(models.Model):
    """
    Group notifications for batch processing and targeting.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User, related_name='notification_groups')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"Group: {self.name}"


class NotificationSchedule(models.Model):
    """
    Scheduled notifications and recurring notification management.
    """
    SCHEDULE_TYPES = [
        ('once', 'Once'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=100)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    schedule_type = models.CharField(max_length=20, choices=SCHEDULE_TYPES)
    cron_expression = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'next_run']),
        ]
    
    def __str__(self):
        return f"Schedule: {self.name}"
