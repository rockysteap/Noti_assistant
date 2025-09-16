"""
Tests for notifications app models.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timezone, timedelta
from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationChannel,
    NotificationDelivery, NotificationSubscription, NotificationGroup,
    NotificationSchedule
)


class NotificationModelTestCase(TestCase):
    """Test cases for Notification model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Test: {title}',
            message_template='Message: {message}',
            notification_type='info'
        )
    
    def test_notification_creation(self):
        """Test Notification creation."""
        notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal'
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.template, self.template)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.notification_type, 'info')
        self.assertEqual(notification.priority, 'normal')
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        self.assertIsNotNone(notification.updated_at)
    
    def test_notification_str(self):
        """Test Notification string representation."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='info',
            priority='normal'
        )
        expected = 'Test Notification (info)'
        self.assertEqual(str(notification), expected)
    
    def test_notification_default_values(self):
        """Test Notification default values."""
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Test message',
            notification_type='info',
            priority='normal'
        )
        
        self.assertFalse(notification.is_read)
        self.assertIsNone(notification.scheduled_at)
        self.assertIsNone(notification.expires_at)
        self.assertEqual(notification.metadata, '{}')
    
    def test_notification_scheduled_at(self):
        """Test Notification scheduled_at field."""
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        notification = Notification.objects.create(
            user=self.user,
            title='Scheduled Notification',
            message='This is scheduled',
            notification_type='info',
            priority='normal',
            scheduled_at=future_time
        )
        
        self.assertEqual(notification.scheduled_at, future_time)
    
    def test_notification_expires_at(self):
        """Test Notification expires_at field."""
        future_time = datetime.now(timezone.utc) + timedelta(days=1)
        notification = Notification.objects.create(
            user=self.user,
            title='Expiring Notification',
            message='This will expire',
            notification_type='info',
            priority='normal',
            expires_at=future_time
        )
        
        self.assertEqual(notification.expires_at, future_time)
    
    def test_notification_metadata(self):
        """Test Notification metadata field."""
        metadata = '{"key": "value", "count": 5}'
        notification = Notification.objects.create(
            user=self.user,
            title='Metadata Test',
            message='Test with metadata',
            notification_type='info',
            priority='normal',
            metadata=metadata
        )
        
        self.assertEqual(notification.metadata, metadata)


class NotificationTemplateModelTestCase(TestCase):
    """Test cases for NotificationTemplate model."""
    
    def test_notification_template_creation(self):
        """Test NotificationTemplate creation."""
        template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Title: {title}',
            message_template='Message: {message}',
            notification_type='info',
            is_active=True
        )
        
        self.assertEqual(template.name, 'test_template')
        self.assertEqual(template.title_template, 'Title: {title}')
        self.assertEqual(template.message_template, 'Message: {message}')
        self.assertEqual(template.notification_type, 'info')
        self.assertTrue(template.is_active)
        self.assertIsNotNone(template.created_at)
        self.assertIsNotNone(template.updated_at)
    
    def test_notification_template_str(self):
        """Test NotificationTemplate string representation."""
        template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Test Title',
            message_template='Test Message',
            notification_type='info'
        )
        expected = 'test_template (info)'
        self.assertEqual(str(template), expected)
    
    def test_notification_template_default_values(self):
        """Test NotificationTemplate default values."""
        template = NotificationTemplate.objects.create(
            name='default_template',
            title_template='Title',
            message_template='Message',
            notification_type='info'
        )
        
        self.assertTrue(template.is_active)
    
    def test_notification_template_unique_name(self):
        """Test NotificationTemplate unique name constraint."""
        NotificationTemplate.objects.create(
            name='unique_template',
            title_template='Title',
            message_template='Message',
            notification_type='info'
        )
        
        # Try to create another template with the same name
        with self.assertRaises(Exception):
            NotificationTemplate.objects.create(
                name='unique_template',
                title_template='Another Title',
                message_template='Another Message',
                notification_type='warning'
            )


class NotificationChannelModelTestCase(TestCase):
    """Test cases for NotificationChannel model."""
    
    def test_notification_channel_creation(self):
        """Test NotificationChannel creation."""
        channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email',
            is_active=True,
            config='{"smtp_server": "smtp.example.com"}'
        )
        
        self.assertEqual(channel.name, 'test_channel')
        self.assertEqual(channel.channel_type, 'email')
        self.assertTrue(channel.is_active)
        self.assertEqual(channel.config, '{"smtp_server": "smtp.example.com"}')
        self.assertIsNotNone(channel.created_at)
        self.assertIsNotNone(channel.updated_at)
    
    def test_notification_channel_str(self):
        """Test NotificationChannel string representation."""
        channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email'
        )
        expected = 'test_channel (email)'
        self.assertEqual(str(channel), expected)
    
    def test_notification_channel_default_values(self):
        """Test NotificationChannel default values."""
        channel = NotificationChannel.objects.create(
            name='default_channel',
            channel_type='sms'
        )
        
        self.assertTrue(channel.is_active)
        self.assertEqual(channel.config, '{}')


class NotificationDeliveryModelTestCase(TestCase):
    """Test cases for NotificationDelivery model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Test message',
            notification_type='info',
            priority='normal'
        )
        self.channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email'
        )
    
    def test_notification_delivery_creation(self):
        """Test NotificationDelivery creation."""
        delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel,
            status='pending',
            external_id='ext_123'
        )
        
        self.assertEqual(delivery.notification, self.notification)
        self.assertEqual(delivery.channel, self.channel)
        self.assertEqual(delivery.status, 'pending')
        self.assertEqual(delivery.external_id, 'ext_123')
        self.assertIsNotNone(delivery.created_at)
        self.assertIsNotNone(delivery.updated_at)
    
    def test_notification_delivery_str(self):
        """Test NotificationDelivery string representation."""
        delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel,
            status='delivered'
        )
        expected = f'{self.notification.title} via {self.channel.name} (delivered)'
        self.assertEqual(str(delivery), expected)
    
    def test_notification_delivery_default_values(self):
        """Test NotificationDelivery default values."""
        delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel
        )
        
        self.assertEqual(delivery.status, 'pending')
        self.assertEqual(delivery.external_id, '')
        self.assertEqual(delivery.error_message, '')
        self.assertIsNone(delivery.delivered_at)


class NotificationSubscriptionModelTestCase(TestCase):
    """Test cases for NotificationSubscription model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email'
        )
    
    def test_notification_subscription_creation(self):
        """Test NotificationSubscription creation."""
        subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel,
            notification_types=['info', 'warning'],
            is_enabled=True
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.channel, self.channel)
        self.assertEqual(subscription.notification_types, ['info', 'warning'])
        self.assertTrue(subscription.is_enabled)
        self.assertIsNotNone(subscription.created_at)
        self.assertIsNotNone(subscription.updated_at)
    
    def test_notification_subscription_str(self):
        """Test NotificationSubscription string representation."""
        subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel
        )
        expected = f'{self.user.username} - {self.channel.name}'
        self.assertEqual(str(subscription), expected)
    
    def test_notification_subscription_default_values(self):
        """Test NotificationSubscription default values."""
        subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel
        )
        
        self.assertEqual(subscription.notification_types, [])
        self.assertTrue(subscription.is_enabled)


class NotificationGroupModelTestCase(TestCase):
    """Test cases for NotificationGroup model."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_notification_group_creation(self):
        """Test NotificationGroup creation."""
        group = NotificationGroup.objects.create(
            name='test_group',
            description='Test notification group',
            is_active=True
        )
        group.users.add(self.user1, self.user2)
        
        self.assertEqual(group.name, 'test_group')
        self.assertEqual(group.description, 'Test notification group')
        self.assertTrue(group.is_active)
        self.assertIn(self.user1, group.users.all())
        self.assertIn(self.user2, group.users.all())
        self.assertIsNotNone(group.created_at)
        self.assertIsNotNone(group.updated_at)
    
    def test_notification_group_str(self):
        """Test NotificationGroup string representation."""
        group = NotificationGroup.objects.create(
            name='test_group',
            description='Test group'
        )
        expected = 'test_group'
        self.assertEqual(str(group), expected)
    
    def test_notification_group_default_values(self):
        """Test NotificationGroup default values."""
        group = NotificationGroup.objects.create(name='default_group')
        
        self.assertEqual(group.description, '')
        self.assertTrue(group.is_active)


class NotificationScheduleModelTestCase(TestCase):
    """Test cases for NotificationSchedule model."""
    
    def setUp(self):
        """Set up test data."""
        self.template = NotificationTemplate.objects.create(
            name='schedule_template',
            title_template='Scheduled: {title}',
            message_template='Scheduled: {message}',
            notification_type='info'
        )
    
    def test_notification_schedule_creation(self):
        """Test NotificationSchedule creation."""
        schedule = NotificationSchedule.objects.create(
            name='test_schedule',
            template=self.template,
            schedule_type='cron',
            cron_expression='0 9 * * 1-5',
            is_active=True
        )
        
        self.assertEqual(schedule.name, 'test_schedule')
        self.assertEqual(schedule.template, self.template)
        self.assertEqual(schedule.schedule_type, 'cron')
        self.assertEqual(schedule.cron_expression, '0 9 * * 1-5')
        self.assertTrue(schedule.is_active)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.updated_at)
    
    def test_notification_schedule_str(self):
        """Test NotificationSchedule string representation."""
        schedule = NotificationSchedule.objects.create(
            name='test_schedule',
            template=self.template,
            schedule_type='cron',
            cron_expression='0 9 * * 1-5'
        )
        expected = 'test_schedule (cron)'
        self.assertEqual(str(schedule), expected)
    
    def test_notification_schedule_default_values(self):
        """Test NotificationSchedule default values."""
        schedule = NotificationSchedule.objects.create(
            name='default_schedule',
            template=self.template,
            schedule_type='interval'
        )
        
        self.assertEqual(schedule.cron_expression, '')
        self.assertTrue(schedule.is_active)
        self.assertIsNone(schedule.last_run)
        self.assertIsNone(schedule.next_run)


class ModelRelationshipsTestCase(TestCase):
    """Test cases for model relationships."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Test: {title}',
            message_template='Message: {message}',
            notification_type='info'
        )
        self.channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            title='Test Notification',
            message='Test message',
            notification_type='info',
            priority='normal'
        )
    
    def test_notification_user_relationship(self):
        """Test Notification-User relationship."""
        self.assertEqual(self.notification.user, self.user)
        self.assertIn(self.notification, self.user.notification_set.all())
    
    def test_notification_template_relationship(self):
        """Test Notification-Template relationship."""
        self.assertEqual(self.notification.template, self.template)
        self.assertIn(self.notification, self.template.notification_set.all())
    
    def test_notification_delivery_relationships(self):
        """Test NotificationDelivery relationships."""
        delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel,
            status='delivered'
        )
        
        self.assertEqual(delivery.notification, self.notification)
        self.assertEqual(delivery.channel, self.channel)
        self.assertIn(delivery, self.notification.deliveries.all())
        self.assertIn(delivery, self.channel.deliveries.all())
    
    def test_notification_subscription_relationships(self):
        """Test NotificationSubscription relationships."""
        subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel,
            notification_types=['info']
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.channel, self.channel)
        self.assertIn(subscription, self.user.notificationsubscription_set.all())
        self.assertIn(subscription, self.channel.subscriptions.all())
    
    def test_cascade_deletion(self):
        """Test cascade deletion behavior."""
        # Create delivery
        delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel,
            status='pending'
        )
        
        # Create subscription
        subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel
        )
        
        # Delete notification
        self.notification.delete()
        
        # Delivery should be deleted (CASCADE)
        self.assertFalse(NotificationDelivery.objects.filter(id=delivery.id).exists())
        
        # Subscription should still exist (no cascade)
        self.assertTrue(NotificationSubscription.objects.filter(id=subscription.id).exists())
        
        # Delete user
        self.user.delete()
        
        # Subscription should be deleted (CASCADE)
        self.assertFalse(NotificationSubscription.objects.filter(id=subscription.id).exists())
