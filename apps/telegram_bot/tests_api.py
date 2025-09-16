"""
Tests for telegram bot app API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from apps.telegram_bot.models import (
    TelegramUser, BotConversation, BotCommand as BotCommandModel,
    BotMessage, BotWebhook, BotAnalytics
)


class TelegramUserAPITestCase(APITestCase):
    """Test cases for Telegram user API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User',
            language_code='en',
            is_premium=True,
            is_verified=True
        )
    
    def test_telegram_user_list_api(self):
        """Test Telegram user list API endpoint."""
        url = reverse('telegramuser-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_telegram_user_detail_api(self):
        """Test Telegram user detail API endpoint."""
        url = reverse('telegramuser-detail', kwargs={'pk': self.telegram_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['telegram_id'], 123456789)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Test')
    
    def test_telegram_user_create_api(self):
        """Test Telegram user creation API endpoint."""
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='newpass123'
        )
        
        url = reverse('telegramuser-list')
        data = {
            'user': new_user.id,
            'telegram_id': 987654321,
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'language_code': 'es',
            'is_premium': False,
            'is_verified': False
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['telegram_id'], 987654321)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['language_code'], 'es')
    
    def test_telegram_user_update_api(self):
        """Test Telegram user update API endpoint."""
        url = reverse('telegramuser-detail', kwargs={'pk': self.telegram_user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'language_code': 'fr'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        self.assertEqual(response.data['language_code'], 'fr')
    
    def test_telegram_user_filtering(self):
        """Test Telegram user filtering."""
        url = reverse('telegramuser-list')
        response = self.client.get(url, {'is_verified': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_telegram_user_search(self):
        """Test Telegram user search."""
        url = reverse('telegramuser-list')
        response = self.client.get(url, {'search': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class BotConversationAPITestCase(APITestCase):
    """Test cases for bot conversation API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser'
        )
        
        self.conversation = BotConversation.objects.create(
            user=self.telegram_user,
            state='waiting_for_input',
            context={'step': 1, 'data': 'test'}
        )
    
    def test_bot_conversation_list_api(self):
        """Test bot conversation list API endpoint."""
        url = reverse('botconversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_conversation_detail_api(self):
        """Test bot conversation detail API endpoint."""
        url = reverse('botconversation-detail', kwargs={'pk': self.conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 'waiting_for_input')
        self.assertEqual(response.data['context'], {'step': 1, 'data': 'test'})
    
    def test_bot_conversation_create_api(self):
        """Test bot conversation creation API endpoint."""
        url = reverse('botconversation-list')
        data = {
            'user': self.telegram_user.id,
            'state': 'processing',
            'context': {'new_step': 2, 'new_data': 'new_test'}
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['state'], 'processing')
        self.assertEqual(response.data['context'], {'new_step': 2, 'new_data': 'new_test'})
    
    def test_bot_conversation_update_api(self):
        """Test bot conversation update API endpoint."""
        url = reverse('botconversation-detail', kwargs={'pk': self.conversation.id})
        data = {
            'state': 'completed',
            'context': {'step': 2, 'data': 'updated'}
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 'completed')
        self.assertEqual(response.data['context'], {'step': 2, 'data': 'updated'})
    
    def test_bot_conversation_filtering(self):
        """Test bot conversation filtering."""
        url = reverse('botconversation-list')
        response = self.client.get(url, {'state': 'waiting_for_input'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class BotCommandAPITestCase(APITestCase):
    """Test cases for bot command API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for command management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.command = BotCommandModel.objects.create(
            command='test',
            description='Test command',
            handler_function='test_handler',
            is_active=True,
            requires_auth=True,
            admin_only=False
        )
    
    def test_bot_command_list_api(self):
        """Test bot command list API endpoint."""
        url = reverse('botcommand-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_command_detail_api(self):
        """Test bot command detail API endpoint."""
        url = reverse('botcommand-detail', kwargs={'pk': self.command.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['command'], 'test')
        self.assertEqual(response.data['description'], 'Test command')
        self.assertEqual(response.data['handler_function'], 'test_handler')
    
    def test_bot_command_create_api(self):
        """Test bot command creation API endpoint."""
        url = reverse('botcommand-list')
        data = {
            'command': 'new_command',
            'description': 'New test command',
            'handler_function': 'new_handler',
            'is_active': True,
            'requires_auth': False,
            'admin_only': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['command'], 'new_command')
        self.assertEqual(response.data['description'], 'New test command')
        self.assertTrue(response.data['admin_only'])
    
    def test_bot_command_update_api(self):
        """Test bot command update API endpoint."""
        url = reverse('botcommand-detail', kwargs={'pk': self.command.id})
        data = {
            'description': 'Updated test command',
            'is_active': False
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated test command')
        self.assertFalse(response.data['is_active'])
    
    def test_bot_command_active_api(self):
        """Test active bot commands API endpoint."""
        url = reverse('botcommand-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
    
    def test_bot_command_filtering(self):
        """Test bot command filtering."""
        url = reverse('botcommand-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class BotMessageAPITestCase(APITestCase):
    """Test cases for bot message API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser'
        )
        
        self.message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            message_type='text',
            content='Hello bot!',
            is_bot_message=False
        )
    
    def test_bot_message_list_api(self):
        """Test bot message list API endpoint."""
        url = reverse('botmessage-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_message_detail_api(self):
        """Test bot message detail API endpoint."""
        url = reverse('botmessage-detail', kwargs={'pk': self.message.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message_id'], 123)
        self.assertEqual(response.data['message_type'], 'text')
        self.assertEqual(response.data['content'], 'Hello bot!')
        self.assertFalse(response.data['is_bot_message'])
    
    def test_bot_message_filtering(self):
        """Test bot message filtering."""
        url = reverse('botmessage-list')
        response = self.client.get(url, {'message_type': 'text'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_message_search(self):
        """Test bot message search."""
        url = reverse('botmessage-list')
        response = self.client.get(url, {'search': 'Hello'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class BotWebhookAPITestCase(APITestCase):
    """Test cases for bot webhook API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for webhook management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.webhook = BotWebhook.objects.create(
            webhook_url='https://example.com/webhook',
            is_active=True,
            secret_token='secret123',
            last_update_id=100
        )
    
    def test_bot_webhook_list_api(self):
        """Test bot webhook list API endpoint."""
        url = reverse('botwebhook-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_webhook_detail_api(self):
        """Test bot webhook detail API endpoint."""
        url = reverse('botwebhook-detail', kwargs={'pk': self.webhook.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['webhook_url'], 'https://example.com/webhook')
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['secret_token'], 'secret123')
    
    def test_bot_webhook_create_api(self):
        """Test bot webhook creation API endpoint."""
        url = reverse('botwebhook-list')
        data = {
            'webhook_url': 'https://new.example.com/webhook',
            'is_active': True,
            'secret_token': 'new_secret',
            'last_update_id': 0
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['webhook_url'], 'https://new.example.com/webhook')
        self.assertTrue(response.data['is_active'])
        self.assertEqual(response.data['secret_token'], 'new_secret')
    
    def test_bot_webhook_update_api(self):
        """Test bot webhook update API endpoint."""
        url = reverse('botwebhook-detail', kwargs={'pk': self.webhook.id})
        data = {
            'is_active': False,
            'last_update_id': 200
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        self.assertEqual(response.data['last_update_id'], 200)
    
    def test_bot_webhook_filtering(self):
        """Test bot webhook filtering."""
        url = reverse('botwebhook-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class BotAnalyticsAPITestCase(APITestCase):
    """Test cases for bot analytics API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        from datetime import date
        self.analytics = BotAnalytics.objects.create(
            date=date.today(),
            total_users=100,
            active_users=50,
            messages_sent=200,
            messages_received=150,
            commands_executed=75,
            errors_count=5
        )
    
    def test_bot_analytics_list_api(self):
        """Test bot analytics list API endpoint."""
        url = reverse('botanalytics-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_analytics_detail_api(self):
        """Test bot analytics detail API endpoint."""
        url = reverse('botanalytics-detail', kwargs={'pk': self.analytics.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_users'], 100)
        self.assertEqual(response.data['active_users'], 50)
        self.assertEqual(response.data['messages_sent'], 200)
        self.assertEqual(response.data['messages_received'], 150)
    
    def test_bot_analytics_filtering(self):
        """Test bot analytics filtering."""
        url = reverse('botanalytics-list')
        response = self.client.get(url, {'date': str(self.analytics.date)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_bot_analytics_ordering(self):
        """Test bot analytics ordering."""
        url = reverse('botanalytics-list')
        response = self.client.get(url, {'ordering': '-date'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Check if results are ordered by date descending
        if len(results) > 1:
            self.assertGreaterEqual(results[0]['date'], results[1]['date'])


class TelegramWebhookTestCase(APITestCase):
    """Test cases for Telegram webhook endpoint."""
    
    def test_telegram_webhook_post(self):
        """Test Telegram webhook POST endpoint."""
        url = reverse('telegram-webhook')
        
        webhook_data = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'username': 'testuser',
                    'first_name': 'Test',
                    'last_name': 'User'
                },
                'text': 'Hello bot!'
            }
        }
        
        response = self.client.post(
            url,
            data=webhook_data,
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')
    
    def test_telegram_webhook_invalid_json(self):
        """Test Telegram webhook with invalid JSON."""
        url = reverse('telegram-webhook')
        
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_telegram_webhook_unauthorized(self):
        """Test Telegram webhook with invalid secret token."""
        url = reverse('telegram-webhook')
        
        webhook_data = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'from': {'id': 123456789},
                'text': 'Hello bot!'
            }
        }
        
        response = self.client.post(
            url,
            data=webhook_data,
            content_type='application/json',
            HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN='invalid_token'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
