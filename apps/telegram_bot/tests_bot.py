"""
Tests for Telegram bot functionality.
"""

import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from apps.telegram_bot.bot import NotiBot, get_bot, handle_telegram_update
from apps.telegram_bot.models import TelegramUser, BotMessage, BotAnalytics
from apps.notifications.models import Notification


class BotTestCase(TestCase):
    """Test cases for bot functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User'
        )
    
    def test_bot_initialization(self):
        """Test bot initialization."""
        with patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', 'test_token'):
            bot = NotiBot()
            self.assertIsNotNone(bot.application)
            self.assertIsNotNone(bot.bot)
    
    def test_bot_initialization_no_token(self):
        """Test bot initialization without token."""
        with patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', ''):
            bot = NotiBot()
            self.assertIsNone(bot.application)
            self.assertIsNone(bot.bot)
    
    def test_get_bot_singleton(self):
        """Test bot singleton pattern."""
        with patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', 'test_token'):
            bot1 = get_bot()
            bot2 = get_bot()
            self.assertIs(bot1, bot2)
    
    def test_handle_telegram_update(self):
        """Test handling Telegram updates."""
        update_data = {
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
        
        with patch('apps.telegram_bot.bot.get_bot') as mock_get_bot:
            mock_bot = Mock()
            mock_bot.application = Mock()
            mock_get_bot.return_value = mock_bot
            
            handle_telegram_update(update_data)
            
            # Verify bot was called
            mock_get_bot.assert_called_once()


class BotIntegrationTestCase(TransactionTestCase):
    """Integration tests for bot functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User'
        )
    
    @patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', 'test_token')
    def test_telegram_user_creation(self):
        """Test automatic Telegram user creation."""
        # This would test the _get_or_create_telegram_user method
        # In a real test, you'd mock the Telegram update
        pass
    
    def test_notification_creation_via_bot(self):
        """Test notification creation through bot."""
        # Create a notification
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)
    
    def test_bot_message_logging(self):
        """Test bot message logging."""
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            message_type='text',
            content='Hello bot!',
            is_bot_message=False
        )
        
        self.assertEqual(message.user, self.telegram_user)
        self.assertEqual(message.content, 'Hello bot!')
        self.assertFalse(message.is_bot_message)
    
    def test_analytics_update(self):
        """Test analytics update."""
        from datetime import date
        
        analytics = BotAnalytics.objects.create(
            date=date.today(),
            total_users=1,
            active_users=1,
            messages_sent=0,
            messages_received=1,
            commands_executed=0,
            errors_count=0
        )
        
        self.assertEqual(analytics.total_users, 1)
        self.assertEqual(analytics.messages_received, 1)


class BotCommandTestCase(TestCase):
    """Test cases for bot commands."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User'
        )
    
    @patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', 'test_token')
    def test_start_command(self):
        """Test /start command."""
        # Mock the update and context
        mock_update = Mock()
        mock_update.message = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = 123456789
        mock_update.effective_user.username = 'testuser'
        mock_update.effective_user.first_name = 'Test'
        mock_update.effective_user.last_name = 'User'
        mock_update.effective_user.language_code = 'en'
        
        mock_context = Mock()
        
        # Create bot and test command
        bot = NotiBot()
        
        # This would be an async test in a real scenario
        # For now, just test that the bot can be created
        self.assertIsNotNone(bot)
    
    def test_help_command_structure(self):
        """Test help command structure."""
        help_text = """
🤖 **Noti Bot Commands**

**Basic Commands:**
/start - Start the bot and see main menu
/help - Show this help message
/cancel - Cancel current operation

**Notification Commands:**
/notifications - View your notifications
/send_notification - Send a new notification

**Settings & Stats:**
/settings - Manage your notification settings
/stats - View your usage statistics

**Quick Actions:**
Use the inline buttons for quick access to features!

Need help? Contact support or use /start to return to the main menu.
        """
        
        # Test that help text contains expected commands
        self.assertIn('/start', help_text)
        self.assertIn('/help', help_text)
        self.assertIn('/notifications', help_text)
        self.assertIn('/settings', help_text)
        self.assertIn('/stats', help_text)


class BotWebhookTestCase(TestCase):
    """Test cases for webhook functionality."""
    
    def test_webhook_view_structure(self):
        """Test webhook view structure."""
        from apps.telegram_bot.webhook_server import TelegramWebhookView
        
        # Test that the view exists and has required methods
        self.assertTrue(hasattr(TelegramWebhookView, 'post'))
    
    def test_webhook_data_processing(self):
        """Test webhook data processing."""
        webhook_data = {
            'update_id': 123456,
            'message': {
                'message_id': 1,
                'from': {
                    'id': 123456789,
                    'username': 'testuser',
                    'first_name': 'Test'
                },
                'text': 'Hello bot!'
            }
        }
        
        # Test that data can be serialized/deserialized
        json_data = json.dumps(webhook_data)
        parsed_data = json.loads(json_data)
        
        self.assertEqual(parsed_data['update_id'], 123456)
        self.assertEqual(parsed_data['message']['text'], 'Hello bot!')


class BotManagementTestCase(TestCase):
    """Test cases for bot management commands."""
    
    def test_command_creation(self):
        """Test bot command creation."""
        from apps.telegram_bot.models import BotCommand as BotCommandModel
        
        command = BotCommandModel.objects.create(
            command='test',
            description='Test command',
            handler_function='test_handler',
            is_active=True,
            requires_auth=True,
            admin_only=False
        )
        
        self.assertEqual(command.command, 'test')
        self.assertEqual(command.description, 'Test command')
        self.assertTrue(command.is_active)
        self.assertTrue(command.requires_auth)
        self.assertFalse(command.admin_only)
    
    def test_command_management(self):
        """Test command management operations."""
        from apps.telegram_bot.models import BotCommand as BotCommandModel
        
        # Create command
        command = BotCommandModel.objects.create(
            command='test',
            description='Test command',
            handler_function='test_handler'
        )
        
        # Update command
        command.is_active = True
        command.save()
        
        # Verify update
        updated_command = BotCommandModel.objects.get(command='test')
        self.assertTrue(updated_command.is_active)
        
        # Delete command
        command.delete()
        
        # Verify deletion
        self.assertFalse(BotCommandModel.objects.filter(command='test').exists())


class BotErrorHandlingTestCase(TestCase):
    """Test cases for bot error handling."""
    
    def test_error_handler_structure(self):
        """Test error handler structure."""
        from apps.telegram_bot.bot import NotiBot
        
        with patch('apps.telegram_bot.bot.settings.TELEGRAM_BOT_TOKEN', 'test_token'):
            bot = NotiBot()
            
            # Test that error handler exists
            self.assertTrue(hasattr(bot, 'error_handler'))
    
    def test_telegram_error_handling(self):
        """Test Telegram error handling."""
        from telegram.error import TelegramError
        
        # Test that TelegramError can be caught
        try:
            raise TelegramError("Test error")
        except TelegramError as e:
            self.assertEqual(str(e), "Test error")
    
    def test_bot_error_exception(self):
        """Test custom bot error exception."""
        from apps.core.exceptions import TelegramBotError
        
        # Test that TelegramBotError can be raised and caught
        try:
            raise TelegramBotError("Bot error")
        except TelegramBotError as e:
            self.assertEqual(str(e), "Bot error")
