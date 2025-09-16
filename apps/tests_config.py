"""
Test configuration and utilities for the notification system.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
import json

from apps.core.models import UserProfile, SystemSettings, AuditLog
from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationChannel,
    NotificationDelivery, NotificationSubscription, NotificationGroup,
    NotificationSchedule
)
from apps.telegram_bot.models import (
    TelegramUser, BotConversation, BotCommand as BotCommandModel,
    BotMessage, BotWebhook, BotAnalytics
)


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_user(username='testuser', email='test@example.com', password='testpass123', **kwargs):
        """Create a test user."""
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            **kwargs
        )
    
    @staticmethod
    def create_user_profile(user, **kwargs):
        """Create a test user profile."""
        defaults = {
            'phone_number': '+1234567890',
            'timezone': 'America/New_York',
            'language': 'en',
            'is_verified': True
        }
        defaults.update(kwargs)
        return UserProfile.objects.create(user=user, **defaults)
    
    @staticmethod
    def create_system_setting(key='test_setting', value='{"test": "value"}', **kwargs):
        """Create a test system setting."""
        defaults = {
            'description': 'Test setting',
            'is_active': True
        }
        defaults.update(kwargs)
        return SystemSettings.objects.create(key=key, value=value, **defaults)
    
    @staticmethod
    def create_audit_log(user, action='test_action', resource='test_resource', **kwargs):
        """Create a test audit log."""
        defaults = {
            'details': '{"test": "details"}',
            'ip_address': '192.168.1.1',
            'user_agent': 'Test Agent'
        }
        defaults.update(kwargs)
        return AuditLog.objects.create(user=user, action=action, resource=resource, **defaults)
    
    @staticmethod
    def create_notification_template(name='test_template', **kwargs):
        """Create a test notification template."""
        defaults = {
            'title_template': 'Test: {title}',
            'message_template': 'Message: {message}',
            'notification_type': 'info',
            'is_active': True
        }
        defaults.update(kwargs)
        return NotificationTemplate.objects.create(name=name, **defaults)
    
    @staticmethod
    def create_notification_channel(name='test_channel', channel_type='email', **kwargs):
        """Create a test notification channel."""
        defaults = {
            'config': '{"smtp_server": "smtp.example.com"}',
            'is_active': True
        }
        defaults.update(kwargs)
        return NotificationChannel.objects.create(name=name, channel_type=channel_type, **defaults)
    
    @staticmethod
    def create_notification(user, template=None, **kwargs):
        """Create a test notification."""
        defaults = {
            'title': 'Test Notification',
            'message': 'This is a test notification',
            'notification_type': 'info',
            'priority': 'normal'
        }
        defaults.update(kwargs)
        if template:
            defaults['template'] = template
        return Notification.objects.create(user=user, **defaults)
    
    @staticmethod
    def create_notification_delivery(notification, channel, **kwargs):
        """Create a test notification delivery."""
        defaults = {
            'status': 'pending',
            'external_id': 'ext_123'
        }
        defaults.update(kwargs)
        return NotificationDelivery.objects.create(
            notification=notification,
            channel=channel,
            **defaults
        )
    
    @staticmethod
    def create_notification_subscription(user, channel, **kwargs):
        """Create a test notification subscription."""
        defaults = {
            'notification_types': ['info', 'warning'],
            'is_enabled': True
        }
        defaults.update(kwargs)
        return NotificationSubscription.objects.create(user=user, channel=channel, **defaults)
    
    @staticmethod
    def create_notification_group(name='test_group', **kwargs):
        """Create a test notification group."""
        defaults = {
            'description': 'Test notification group',
            'is_active': True
        }
        defaults.update(kwargs)
        return NotificationGroup.objects.create(name=name, **defaults)
    
    @staticmethod
    def create_notification_schedule(template, **kwargs):
        """Create a test notification schedule."""
        defaults = {
            'name': 'test_schedule',
            'schedule_type': 'cron',
            'cron_expression': '0 9 * * 1-5',
            'is_active': True
        }
        defaults.update(kwargs)
        return NotificationSchedule.objects.create(template=template, **defaults)
    
    @staticmethod
    def create_telegram_user(user, telegram_id=123456789, **kwargs):
        """Create a test Telegram user."""
        defaults = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_bot': False,
            'is_premium': False,
            'is_verified': False
        }
        defaults.update(kwargs)
        return TelegramUser.objects.create(user=user, telegram_id=telegram_id, **defaults)
    
    @staticmethod
    def create_bot_conversation(telegram_user, **kwargs):
        """Create a test bot conversation."""
        defaults = {
            'state': 'idle',
            'context': {}
        }
        defaults.update(kwargs)
        return BotConversation.objects.create(user=telegram_user, **defaults)
    
    @staticmethod
    def create_bot_command(command='test', **kwargs):
        """Create a test bot command."""
        defaults = {
            'description': 'Test command',
            'handler_function': 'test_handler',
            'is_active': True,
            'requires_auth': True,
            'admin_only': False
        }
        defaults.update(kwargs)
        return BotCommandModel.objects.create(command=command, **defaults)
    
    @staticmethod
    def create_bot_message(telegram_user, message_id=123, **kwargs):
        """Create a test bot message."""
        defaults = {
            'message_type': 'text',
            'content': 'Test message',
            'is_bot_message': False
        }
        defaults.update(kwargs)
        return BotMessage.objects.create(user=telegram_user, message_id=message_id, **defaults)
    
    @staticmethod
    def create_bot_webhook(webhook_url='https://example.com/webhook', **kwargs):
        """Create a test bot webhook."""
        defaults = {
            'is_active': True,
            'secret_token': 'secret123',
            'last_update_id': 0
        }
        defaults.update(kwargs)
        return BotWebhook.objects.create(webhook_url=webhook_url, **defaults)
    
    @staticmethod
    def create_bot_analytics(date=None, **kwargs):
        """Create a test bot analytics record."""
        if date is None:
            from datetime import date
            date = date.today()
        
        defaults = {
            'total_users': 100,
            'active_users': 50,
            'messages_sent': 200,
            'messages_received': 150,
            'commands_executed': 75,
            'errors_count': 5
        }
        defaults.update(kwargs)
        return BotAnalytics.objects.create(date=date, **defaults)


class MockTelegramBot:
    """Mock Telegram bot for testing."""
    
    def __init__(self, token='test_token'):
        self.token = token
        self.webhook_url = None
        self.commands = []
        self.messages_sent = []
        self.callbacks_handled = []
    
    def set_webhook(self, url, secret_token=None):
        """Mock set webhook."""
        self.webhook_url = url
        self.secret_token = secret_token
        return True
    
    def delete_webhook(self):
        """Mock delete webhook."""
        self.webhook_url = None
        self.secret_token = None
        return True
    
    def set_my_commands(self, commands):
        """Mock set commands."""
        self.commands = commands
        return True
    
    def send_message(self, chat_id, text, **kwargs):
        """Mock send message."""
        message = {
            'chat_id': chat_id,
            'text': text,
            'message_id': len(self.messages_sent) + 1,
            **kwargs
        }
        self.messages_sent.append(message)
        return message
    
    def send_photo(self, chat_id, photo, **kwargs):
        """Mock send photo."""
        message = {
            'chat_id': chat_id,
            'photo': photo,
            'message_id': len(self.messages_sent) + 1,
            **kwargs
        }
        self.messages_sent.append(message)
        return message
    
    def send_document(self, chat_id, document, **kwargs):
        """Mock send document."""
        message = {
            'chat_id': chat_id,
            'document': document,
            'message_id': len(self.messages_sent) + 1,
            **kwargs
        }
        self.messages_sent.append(message)
        return message
    
    def answer_callback_query(self, callback_query_id, text=None, **kwargs):
        """Mock answer callback query."""
        callback = {
            'callback_query_id': callback_query_id,
            'text': text,
            **kwargs
        }
        self.callbacks_handled.append(callback)
        return callback


class TestUtilities:
    """Utility functions for testing."""
    
    @staticmethod
    def create_authenticated_client(user):
        """Create an authenticated API client."""
        from rest_framework.test import APIClient
        from rest_framework.authtoken.models import Token
        
        client = APIClient()
        token = Token.objects.create(user=user)
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client
    
    @staticmethod
    def create_webhook_payload(update_id=123456, message_text='Hello bot!', **kwargs):
        """Create a mock webhook payload."""
        defaults = {
            'update_id': update_id,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'username': 'testuser',
                    'first_name': 'Test',
                    'last_name': 'User'
                },
                'text': message_text,
                'chat': {
                    'id': 123456789,
                    'type': 'private'
                }
            }
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def create_callback_query_payload(update_id=123456, data='test_callback', **kwargs):
        """Create a mock callback query payload."""
        defaults = {
            'update_id': update_id,
            'callback_query': {
                'id': 'callback_123',
                'from': {
                    'id': 123456789,
                    'username': 'testuser',
                    'first_name': 'Test',
                    'last_name': 'User'
                },
                'data': data,
                'message': {
                    'message_id': 1,
                    'chat': {
                        'id': 123456789,
                        'type': 'private'
                    }
                }
            }
        }
        defaults.update(kwargs)
        return defaults
    
    @staticmethod
    def assert_notification_created(user, title, message, notification_type='info'):
        """Assert that a notification was created."""
        notification = Notification.objects.filter(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        ).first()
        assert notification is not None, f"Notification not found: {title}"
        return notification
    
    @staticmethod
    def assert_audit_log_created(user, action, resource):
        """Assert that an audit log was created."""
        audit_log = AuditLog.objects.filter(
            user=user,
            action=action,
            resource=resource
        ).first()
        assert audit_log is not None, f"Audit log not found: {action} on {resource}"
        return audit_log
    
    @staticmethod
    def assert_telegram_user_created(user, telegram_id):
        """Assert that a Telegram user was created."""
        telegram_user = TelegramUser.objects.filter(
            user=user,
            telegram_id=telegram_id
        ).first()
        assert telegram_user is not None, f"Telegram user not found: {telegram_id}"
        return telegram_user
    
    @staticmethod
    def assert_bot_message_created(telegram_user, content):
        """Assert that a bot message was created."""
        message = BotMessage.objects.filter(
            user=telegram_user,
            content=content
        ).first()
        assert message is not None, f"Bot message not found: {content}"
        return message


class TestConstants:
    """Constants for testing."""
    
    # Test user data
    TEST_USERNAME = 'testuser'
    TEST_EMAIL = 'test@example.com'
    TEST_PASSWORD = 'testpass123'
    
    # Test Telegram data
    TEST_TELEGRAM_ID = 123456789
    TEST_TELEGRAM_USERNAME = 'testuser'
    TEST_TELEGRAM_FIRST_NAME = 'Test'
    TEST_TELEGRAM_LAST_NAME = 'User'
    
    # Test notification data
    TEST_NOTIFICATION_TITLE = 'Test Notification'
    TEST_NOTIFICATION_MESSAGE = 'This is a test notification'
    TEST_NOTIFICATION_TYPE = 'info'
    TEST_NOTIFICATION_PRIORITY = 'normal'
    
    # Test template data
    TEST_TEMPLATE_NAME = 'test_template'
    TEST_TEMPLATE_TITLE = 'Test: {title}'
    TEST_TEMPLATE_MESSAGE = 'Message: {message}'
    
    # Test channel data
    TEST_CHANNEL_NAME = 'test_channel'
    TEST_CHANNEL_TYPE = 'email'
    TEST_CHANNEL_CONFIG = '{"smtp_server": "smtp.example.com"}'
    
    # Test webhook data
    TEST_WEBHOOK_URL = 'https://example.com/webhook'
    TEST_WEBHOOK_SECRET = 'secret123'
    
    # Test API responses
    SUCCESS_STATUS = 200
    CREATED_STATUS = 201
    BAD_REQUEST_STATUS = 400
    UNAUTHORIZED_STATUS = 401
    FORBIDDEN_STATUS = 403
    NOT_FOUND_STATUS = 404
    RATE_LIMITED_STATUS = 429
    
    # Test pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Test timeouts
    DEFAULT_TIMEOUT = 30
    LONG_TIMEOUT = 60
    
    # Test retry counts
    MAX_RETRIES = 3
    RETRY_DELAY = 1
