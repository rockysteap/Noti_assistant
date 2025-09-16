"""
Tests for telegram bot app models.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime, timezone, timedelta
from apps.telegram_bot.models import (
    TelegramUser, BotConversation, BotCommand as BotCommandModel,
    BotMessage, BotWebhook, BotAnalytics
)


class TelegramUserModelTestCase(TestCase):
    """Test cases for TelegramUser model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_telegram_user_creation(self):
        """Test TelegramUser creation."""
        telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User',
            language_code='en',
            is_bot=False,
            is_premium=True,
            is_verified=True
        )
        
        self.assertEqual(telegram_user.user, self.user)
        self.assertEqual(telegram_user.telegram_id, 123456789)
        self.assertEqual(telegram_user.username, 'testuser')
        self.assertEqual(telegram_user.first_name, 'Test')
        self.assertEqual(telegram_user.last_name, 'User')
        self.assertEqual(telegram_user.language_code, 'en')
        self.assertFalse(telegram_user.is_bot)
        self.assertTrue(telegram_user.is_premium)
        self.assertTrue(telegram_user.is_verified)
        self.assertIsNotNone(telegram_user.created_at)
        self.assertIsNotNone(telegram_user.updated_at)
    
    def test_telegram_user_str(self):
        """Test TelegramUser string representation."""
        telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789,
            username='testuser'
        )
        expected = '@testuser'
        self.assertEqual(str(telegram_user), expected)
    
    def test_telegram_user_str_no_username(self):
        """Test TelegramUser string representation without username."""
        telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789
        )
        expected = 'Telegram User 123456789'
        self.assertEqual(str(telegram_user), expected)
    
    def test_telegram_user_default_values(self):
        """Test TelegramUser default values."""
        telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789
        )
        
        self.assertEqual(telegram_user.username, '')
        self.assertEqual(telegram_user.first_name, '')
        self.assertEqual(telegram_user.last_name, '')
        self.assertEqual(telegram_user.language_code, 'en')
        self.assertFalse(telegram_user.is_bot)
        self.assertFalse(telegram_user.is_premium)
        self.assertFalse(telegram_user.is_verified)
    
    def test_telegram_user_unique_telegram_id(self):
        """Test TelegramUser unique telegram_id constraint."""
        TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789
        )
        
        # Try to create another user with the same telegram_id
        with self.assertRaises(Exception):
            TelegramUser.objects.create(
                user=self.user,
                telegram_id=123456789
            )
    
    def test_telegram_user_one_to_one_relationship(self):
        """Test one-to-one relationship with User."""
        telegram_user = TelegramUser.objects.create(
            user=self.user,
            telegram_id=123456789
        )
        
        # Test forward relationship
        self.assertEqual(telegram_user.user, self.user)
        
        # Test reverse relationship
        self.assertEqual(self.user.telegram_user, telegram_user)
        
        # Test that only one TelegramUser can exist per User
        with self.assertRaises(Exception):
            TelegramUser.objects.create(
                user=self.user,
                telegram_id=987654321
            )


class BotConversationModelTestCase(TestCase):
    """Test cases for BotConversation model."""
    
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
            username='testuser'
        )
    
    def test_bot_conversation_creation(self):
        """Test BotConversation creation."""
        conversation = BotConversation.objects.create(
            user=self.telegram_user,
            state='waiting_for_input',
            context={'step': 1, 'data': 'test'}
        )
        
        self.assertEqual(conversation.user, self.telegram_user)
        self.assertEqual(conversation.state, 'waiting_for_input')
        self.assertEqual(conversation.context, {'step': 1, 'data': 'test'})
        self.assertIsNotNone(conversation.last_activity)
        self.assertIsNotNone(conversation.created_at)
    
    def test_bot_conversation_str(self):
        """Test BotConversation string representation."""
        conversation = BotConversation.objects.create(
            user=self.telegram_user,
            state='processing'
        )
        expected = f'{self.telegram_user} - processing'
        self.assertEqual(str(conversation), expected)
    
    def test_bot_conversation_default_values(self):
        """Test BotConversation default values."""
        conversation = BotConversation.objects.create(
            user=self.telegram_user
        )
        
        self.assertEqual(conversation.state, 'idle')
        self.assertEqual(conversation.context, {})
    
    def test_bot_conversation_state_choices(self):
        """Test BotConversation state choices."""
        valid_states = ['idle', 'waiting_for_input', 'processing', 'completed', 'cancelled']
        
        for state in valid_states:
            conversation = BotConversation.objects.create(
                user=self.telegram_user,
                state=state
            )
            self.assertEqual(conversation.state, state)
    
    def test_bot_conversation_ordering(self):
        """Test BotConversation ordering by last_activity."""
        # Create conversations with different last_activity times
        conv1 = BotConversation.objects.create(
            user=self.telegram_user,
            state='idle'
        )
        conv2 = BotConversation.objects.create(
            user=self.telegram_user,
            state='processing'
        )
        
        # Get all conversations
        conversations = BotConversation.objects.all()
        
        # Should be ordered by last_activity descending (newest first)
        self.assertEqual(conversations[0], conv2)
        self.assertEqual(conversations[1], conv1)


class BotCommandModelTestCase(TestCase):
    """Test cases for BotCommand model."""
    
    def test_bot_command_creation(self):
        """Test BotCommand creation."""
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
        self.assertEqual(command.handler_function, 'test_handler')
        self.assertTrue(command.is_active)
        self.assertTrue(command.requires_auth)
        self.assertFalse(command.admin_only)
        self.assertIsNotNone(command.created_at)
        self.assertIsNotNone(command.updated_at)
    
    def test_bot_command_str(self):
        """Test BotCommand string representation."""
        command = BotCommandModel.objects.create(
            command='test',
            description='Test command'
        )
        expected = '/test - Test command'
        self.assertEqual(str(command), expected)
    
    def test_bot_command_default_values(self):
        """Test BotCommand default values."""
        command = BotCommandModel.objects.create(
            command='default',
            description='Default command'
        )
        
        self.assertTrue(command.is_active)
        self.assertTrue(command.requires_auth)
        self.assertFalse(command.admin_only)
    
    def test_bot_command_unique_command(self):
        """Test BotCommand unique command constraint."""
        BotCommandModel.objects.create(
            command='unique_command',
            description='First command'
        )
        
        # Try to create another command with the same command name
        with self.assertRaises(Exception):
            BotCommandModel.objects.create(
                command='unique_command',
                description='Second command'
            )


class BotMessageModelTestCase(TestCase):
    """Test cases for BotMessage model."""
    
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
            username='testuser'
        )
    
    def test_bot_message_creation(self):
        """Test BotMessage creation."""
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            message_type='text',
            content='Hello bot!',
            is_bot_message=False
        )
        
        self.assertEqual(message.user, self.telegram_user)
        self.assertEqual(message.message_id, 123)
        self.assertEqual(message.message_type, 'text')
        self.assertEqual(message.content, 'Hello bot!')
        self.assertFalse(message.is_bot_message)
        self.assertIsNone(message.reply_to_message)
        self.assertIsNotNone(message.created_at)
    
    def test_bot_message_str(self):
        """Test BotMessage string representation."""
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            message_type='text',
            content='Hello bot!'
        )
        expected = f'{self.telegram_user} - text - {message.created_at}'
        self.assertEqual(str(message), expected)
    
    def test_bot_message_default_values(self):
        """Test BotMessage default values."""
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123
        )
        
        self.assertEqual(message.message_type, 'text')
        self.assertEqual(message.content, '')
        self.assertFalse(message.is_bot_message)
        self.assertIsNone(message.reply_to_message)
    
    def test_bot_message_reply_relationship(self):
        """Test BotMessage reply relationship."""
        original_message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            content='Original message'
        )
        
        reply_message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=124,
            content='Reply message',
            reply_to_message=original_message
        )
        
        self.assertEqual(reply_message.reply_to_message, original_message)
    
    def test_bot_message_ordering(self):
        """Test BotMessage ordering by created_at."""
        # Create messages
        msg1 = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            content='First message'
        )
        msg2 = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=124,
            content='Second message'
        )
        
        # Get all messages
        messages = BotMessage.objects.all()
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(messages[0], msg2)
        self.assertEqual(messages[1], msg1)


class BotWebhookModelTestCase(TestCase):
    """Test cases for BotWebhook model."""
    
    def test_bot_webhook_creation(self):
        """Test BotWebhook creation."""
        webhook = BotWebhook.objects.create(
            webhook_url='https://example.com/webhook',
            is_active=True,
            secret_token='secret123',
            last_update_id=100
        )
        
        self.assertEqual(webhook.webhook_url, 'https://example.com/webhook')
        self.assertTrue(webhook.is_active)
        self.assertEqual(webhook.secret_token, 'secret123')
        self.assertEqual(webhook.last_update_id, 100)
        self.assertIsNotNone(webhook.created_at)
        self.assertIsNotNone(webhook.updated_at)
    
    def test_bot_webhook_str(self):
        """Test BotWebhook string representation."""
        webhook = BotWebhook.objects.create(
            webhook_url='https://example.com/webhook'
        )
        expected = 'Webhook: https://example.com/webhook'
        self.assertEqual(str(webhook), expected)
    
    def test_bot_webhook_default_values(self):
        """Test BotWebhook default values."""
        webhook = BotWebhook.objects.create(
            webhook_url='https://example.com/webhook'
        )
        
        self.assertTrue(webhook.is_active)
        self.assertEqual(webhook.secret_token, '')
        self.assertEqual(webhook.last_update_id, 0)


class BotAnalyticsModelTestCase(TestCase):
    """Test cases for BotAnalytics model."""
    
    def test_bot_analytics_creation(self):
        """Test BotAnalytics creation."""
        from datetime import date
        today = date.today()
        
        analytics = BotAnalytics.objects.create(
            date=today,
            total_users=100,
            active_users=50,
            messages_sent=200,
            messages_received=150,
            commands_executed=75,
            errors_count=5
        )
        
        self.assertEqual(analytics.date, today)
        self.assertEqual(analytics.total_users, 100)
        self.assertEqual(analytics.active_users, 50)
        self.assertEqual(analytics.messages_sent, 200)
        self.assertEqual(analytics.messages_received, 150)
        self.assertEqual(analytics.commands_executed, 75)
        self.assertEqual(analytics.errors_count, 5)
        self.assertIsNotNone(analytics.created_at)
    
    def test_bot_analytics_str(self):
        """Test BotAnalytics string representation."""
        from datetime import date
        today = date.today()
        
        analytics = BotAnalytics.objects.create(date=today)
        expected = f'Analytics for {today}'
        self.assertEqual(str(analytics), expected)
    
    def test_bot_analytics_default_values(self):
        """Test BotAnalytics default values."""
        from datetime import date
        today = date.today()
        
        analytics = BotAnalytics.objects.create(date=today)
        
        self.assertEqual(analytics.total_users, 0)
        self.assertEqual(analytics.active_users, 0)
        self.assertEqual(analytics.messages_sent, 0)
        self.assertEqual(analytics.messages_received, 0)
        self.assertEqual(analytics.commands_executed, 0)
        self.assertEqual(analytics.errors_count, 0)
    
    def test_bot_analytics_unique_date(self):
        """Test BotAnalytics unique date constraint."""
        from datetime import date
        today = date.today()
        
        BotAnalytics.objects.create(date=today)
        
        # Try to create another analytics record for the same date
        with self.assertRaises(Exception):
            BotAnalytics.objects.create(date=today)
    
    def test_bot_analytics_ordering(self):
        """Test BotAnalytics ordering by date."""
        from datetime import date, timedelta
        
        yesterday = date.today() - timedelta(days=1)
        today = date.today()
        
        # Create analytics records
        analytics1 = BotAnalytics.objects.create(date=yesterday)
        analytics2 = BotAnalytics.objects.create(date=today)
        
        # Get all analytics
        analytics = BotAnalytics.objects.all()
        
        # Should be ordered by date descending (newest first)
        self.assertEqual(analytics[0], analytics2)
        self.assertEqual(analytics[1], analytics1)


class ModelRelationshipsTestCase(TestCase):
    """Test cases for model relationships."""
    
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
            username='testuser'
        )
    
    def test_telegram_user_user_relationship(self):
        """Test TelegramUser-User relationship."""
        self.assertEqual(self.telegram_user.user, self.user)
        self.assertEqual(self.user.telegram_user, self.telegram_user)
    
    def test_telegram_user_conversation_relationship(self):
        """Test TelegramUser-BotConversation relationship."""
        conversation = BotConversation.objects.create(
            user=self.telegram_user,
            state='idle'
        )
        
        self.assertEqual(conversation.user, self.telegram_user)
        self.assertIn(conversation, self.telegram_user.conversations.all())
    
    def test_telegram_user_message_relationship(self):
        """Test TelegramUser-BotMessage relationship."""
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            content='Test message'
        )
        
        self.assertEqual(message.user, self.telegram_user)
        self.assertIn(message, self.telegram_user.messages.all())
    
    def test_bot_message_reply_relationship(self):
        """Test BotMessage reply relationship."""
        original_message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            content='Original'
        )
        
        reply_message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=124,
            content='Reply',
            reply_to_message=original_message
        )
        
        self.assertEqual(reply_message.reply_to_message, original_message)
    
    def test_cascade_deletion(self):
        """Test cascade deletion behavior."""
        # Create conversation and message
        conversation = BotConversation.objects.create(
            user=self.telegram_user,
            state='idle'
        )
        message = BotMessage.objects.create(
            user=self.telegram_user,
            message_id=123,
            content='Test message'
        )
        
        # Delete telegram user
        self.telegram_user.delete()
        
        # Conversation should be deleted (CASCADE)
        self.assertFalse(BotConversation.objects.filter(id=conversation.id).exists())
        
        # Message should be deleted (CASCADE)
        self.assertFalse(BotMessage.objects.filter(id=message.id).exists())
        
        # User should still exist (no cascade)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())
