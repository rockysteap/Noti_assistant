"""
Integration tests for the entire notification system.
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
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


class NotificationWorkflowTestCase(APITestCase):
    """Test complete notification workflow from creation to delivery."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create notification template
        self.template = NotificationTemplate.objects.create(
            name='welcome_template',
            title_template='Welcome {user}!',
            message_template='Hello {user}, welcome to our service!',
            notification_type='info'
        )
        
        # Create notification channel
        self.channel = NotificationChannel.objects.create(
            name='email_channel',
            channel_type='email',
            config='{"smtp_server": "smtp.example.com"}',
            is_active=True
        )
        
        # Create notification subscription
        self.subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel,
            notification_types=['info', 'warning'],
            is_enabled=True
        )
    
    def test_complete_notification_workflow(self):
        """Test complete notification workflow."""
        # 1. Create notification
        notification_data = {
            'title': 'Welcome Test User!',
            'message': 'Hello Test User, welcome to our service!',
            'notification_type': 'info',
            'priority': 'normal'
        }
        
        url = reverse('notification-list')
        response = self.client.post(url, notification_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification_id = response.data['id']
        
        # 2. Verify notification was created
        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Welcome Test User!')
        self.assertFalse(notification.is_read)
        
        # 3. Create delivery record
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            channel=self.channel,
            status='pending',
            external_id='delivery_123'
        )
        
        self.assertEqual(delivery.notification, notification)
        self.assertEqual(delivery.channel, self.channel)
        self.assertEqual(delivery.status, 'pending')
        
        # 4. Simulate successful delivery
        delivery.status = 'delivered'
        delivery.delivered_at = datetime.now(timezone.utc)
        delivery.save()
        
        # 5. Mark notification as read
        url = reverse('notification-mark-read', kwargs={'pk': notification_id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        
        # 6. Verify final state
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'delivered')
        self.assertIsNotNone(delivery.delivered_at)
    
    def test_notification_template_workflow(self):
        """Test notification template workflow."""
        # 1. Create template
        template_data = {
            'name': 'test_workflow_template',
            'title_template': 'Test: {title}',
            'message_template': 'Message: {message}',
            'notification_type': 'warning',
            'is_active': True
        }
        
        url = reverse('notificationtemplate-list')
        response = self.client.post(url, template_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        template_id = response.data['id']
        
        # 2. Use template to create notification
        notification_data = {
            'template': template_id,
            'title': 'Test Title',
            'message': 'Test Message',
            'notification_type': 'warning',
            'priority': 'high'
        }
        
        url = reverse('notification-list')
        response = self.client.post(url, notification_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification_id = response.data['id']
        
        # 3. Verify template was used
        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.template.id, template_id)
        self.assertEqual(notification.notification_type, 'warning')
    
    def test_notification_subscription_workflow(self):
        """Test notification subscription workflow."""
        # 1. Create new channel
        channel_data = {
            'name': 'sms_channel',
            'channel_type': 'sms',
            'config': '{"api_key": "test_key"}',
            'is_active': True
        }
        
        url = reverse('notificationchannel-list')
        response = self.client.post(url, channel_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        channel_id = response.data['id']
        
        # 2. Subscribe to new channel
        subscription_data = {
            'channel': channel_id,
            'notification_types': ['error', 'success'],
            'is_enabled': True
        }
        
        url = reverse('notificationsubscription-list')
        response = self.client.post(url, subscription_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        subscription_id = response.data['id']
        
        # 3. Verify subscription
        subscription = NotificationSubscription.objects.get(id=subscription_id)
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.channel.id, channel_id)
        self.assertEqual(subscription.notification_types, ['error', 'success'])
        self.assertTrue(subscription.is_enabled)
        
        # 4. Update subscription
        update_data = {
            'notification_types': ['error', 'success', 'warning'],
            'is_enabled': False
        }
        
        url = reverse('notificationsubscription-detail', kwargs={'pk': subscription_id})
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notification_types'], ['error', 'success', 'warning'])
        self.assertFalse(response.data['is_enabled'])


class TelegramBotWorkflowTestCase(APITestCase):
    """Test complete Telegram bot workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create Telegram user
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User',
            language_code='en'
        )
        
        # Create bot command
        self.command = BotCommandModel.objects.create(
            command='test',
            description='Test command',
            handler_function='test_handler',
            is_active=True,
            requires_auth=True,
            admin_only=False
        )
    
    def test_telegram_user_workflow(self):
        """Test Telegram user workflow."""
        # 1. Create new user
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='newpass123'
        )
        
        # 2. Create Telegram user
        telegram_user_data = {
            'user': new_user.id,
            'telegram_id': 987654321,
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'language_code': 'es',
            'is_premium': True,
            'is_verified': True
        }
        
        url = reverse('telegramuser-list')
        response = self.client.post(url, telegram_user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        telegram_user_id = response.data['id']
        
        # 3. Create conversation
        conversation_data = {
            'user': telegram_user_id,
            'state': 'waiting_for_input',
            'context': {'step': 1, 'data': 'test'}
        }
        
        url = reverse('botconversation-list')
        response = self.client.post(url, conversation_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        conversation_id = response.data['id']
        
        # 4. Create message
        message_data = {
            'user': telegram_user_id,
            'message_id': 123,
            'message_type': 'text',
            'content': 'Hello bot!',
            'is_bot_message': False
        }
        
        url = reverse('botmessage-list')
        response = self.client.post(url, message_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        message_id = response.data['id']
        
        # 5. Update conversation
        conversation_update = {
            'state': 'processing',
            'context': {'step': 2, 'data': 'updated'}
        }
        
        url = reverse('botconversation-detail', kwargs={'pk': conversation_id})
        response = self.client.patch(url, conversation_update)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 'processing')
        
        # 6. Verify relationships
        telegram_user = TelegramUser.objects.get(id=telegram_user_id)
        self.assertEqual(telegram_user.user, new_user)
        self.assertEqual(telegram_user.telegram_id, 987654321)
        
        conversation = BotConversation.objects.get(id=conversation_id)
        self.assertEqual(conversation.user, telegram_user)
        self.assertEqual(conversation.state, 'processing')
        
        message = BotMessage.objects.get(id=message_id)
        self.assertEqual(message.user, telegram_user)
        self.assertEqual(message.content, 'Hello bot!')
    
    def test_bot_command_workflow(self):
        """Test bot command workflow."""
        # 1. Create command
        command_data = {
            'command': 'workflow_test',
            'description': 'Workflow test command',
            'handler_function': 'workflow_handler',
            'is_active': True,
            'requires_auth': False,
            'admin_only': True
        }
        
        url = reverse('botcommand-list')
        response = self.client.post(url, command_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        command_id = response.data['id']
        
        # 2. Update command
        update_data = {
            'description': 'Updated workflow test command',
            'is_active': False
        }
        
        url = reverse('botcommand-detail', kwargs={'pk': command_id})
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated workflow test command')
        self.assertFalse(response.data['is_active'])
        
        # 3. Get active commands
        url = reverse('botcommand-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_webhook_workflow(self):
        """Test webhook workflow."""
        # 1. Create webhook
        webhook_data = {
            'webhook_url': 'https://example.com/webhook',
            'is_active': True,
            'secret_token': 'secret123',
            'last_update_id': 0
        }
        
        url = reverse('botwebhook-list')
        response = self.client.post(url, webhook_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        webhook_id = response.data['id']
        
        # 2. Update webhook
        update_data = {
            'last_update_id': 100,
            'is_active': False
        }
        
        url = reverse('botwebhook-detail', kwargs={'pk': webhook_id})
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['last_update_id'], 100)
        self.assertFalse(response.data['is_active'])
        
        # 3. Test webhook endpoint
        webhook_url = reverse('telegram-webhook')
        webhook_payload = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'username': 'testuser',
                    'first_name': 'Test',
                    'last_name': 'User'
                },
                'text': '/test'
            }
        }
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')


class SystemIntegrationTestCase(APITestCase):
    """Test system-wide integration scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create system settings
        self.setting = SystemSettings.objects.create(
            key='test_integration_setting',
            value='{"test": "value"}',
            description='Test integration setting',
            is_active=True
        )
        
        # Create audit log
        self.audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource',
            details='{"test": "details"}',
            ip_address='192.168.1.1',
            user_agent='Test Agent'
        )
    
    def test_system_settings_workflow(self):
        """Test system settings workflow."""
        # 1. Create setting
        setting_data = {
            'key': 'integration_test_setting',
            'value': '{"integration": "test"}',
            'description': 'Integration test setting',
            'is_active': True
        }
        
        url = reverse('systemsettings-list')
        response = self.client.post(url, setting_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        setting_id = response.data['id']
        
        # 2. Update setting
        update_data = {
            'value': '{"integration": "updated"}',
            'is_active': False
        }
        
        url = reverse('systemsettings-detail', kwargs={'pk': setting_id})
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], '{"integration": "updated"}')
        self.assertFalse(response.data['is_active'])
        
        # 3. Verify setting
        setting = SystemSettings.objects.get(id=setting_id)
        self.assertEqual(setting.value, '{"integration": "updated"}')
        self.assertFalse(setting.is_active)
    
    def test_audit_log_workflow(self):
        """Test audit log workflow."""
        # 1. Create audit log
        audit_data = {
            'action': 'integration_test_action',
            'resource': 'integration_test_resource',
            'details': '{"integration": "test"}',
            'ip_address': '10.0.0.1',
            'user_agent': 'Integration Test Agent'
        }
        
        url = reverse('auditlog-list')
        response = self.client.post(url, audit_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        audit_id = response.data['id']
        
        # 2. Verify audit log
        audit_log = AuditLog.objects.get(id=audit_id)
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'integration_test_action')
        self.assertEqual(audit_log.resource, 'integration_test_resource')
        self.assertEqual(audit_log.details, '{"integration": "test"}')
        
        # 3. Test audit log filtering
        url = reverse('auditlog-list')
        response = self.client.get(url, {'action': 'integration_test_action'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_user_profile_workflow(self):
        """Test user profile workflow."""
        # 1. Create user profile
        profile_data = {
            'phone_number': '+1234567890',
            'timezone': 'America/New_York',
            'language': 'en',
            'is_verified': True
        }
        
        url = reverse('userprofile-list')
        response = self.client.post(url, profile_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        profile_id = response.data['id']
        
        # 2. Update profile
        update_data = {
            'phone_number': '+9876543210',
            'timezone': 'Europe/London',
            'language': 'es'
        }
        
        url = reverse('userprofile-detail', kwargs={'pk': profile_id})
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '+9876543210')
        self.assertEqual(response.data['timezone'], 'Europe/London')
        self.assertEqual(response.data['language'], 'es')
        
        # 3. Verify profile
        profile = UserProfile.objects.get(id=profile_id)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+9876543210')
        self.assertEqual(profile.timezone, 'Europe/London')
        self.assertEqual(profile.language, 'es')


class PerformanceTestCase(APITestCase):
    """Test performance-related scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        # Create multiple users for pagination testing
        for i in range(50):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
    
    def test_pagination_performance(self):
        """Test pagination performance."""
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Should have pagination
        self.assertGreater(response.data['count'], 20)  # More than page size
        self.assertIsNotNone(response.data['next'])  # Has next page
        self.assertLessEqual(len(response.data['results']), 20)  # Page size limit
    
    def test_search_performance(self):
        """Test search performance."""
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'user'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_ordering_performance(self):
        """Test ordering performance."""
        url = reverse('user-list')
        response = self.client.get(url, {'ordering': 'username'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Check if results are ordered by username
        if len(results) > 1:
            self.assertLessEqual(results[0]['username'], results[1]['username'])
