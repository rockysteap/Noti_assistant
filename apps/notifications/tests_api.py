"""
Tests for notifications app API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import datetime, timezone, timedelta
from apps.notifications.models import (
    Notification, NotificationTemplate, NotificationChannel,
    NotificationDelivery, NotificationSubscription, NotificationGroup,
    NotificationSchedule
)


class NotificationAPITestCase(APITestCase):
    """Test cases for notification API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Test: {title}',
            message_template='Message: {message}',
            notification_type='info'
        )
        
        self.notification = Notification.objects.create(
            user=self.user,
            template=self.template,
            title='Test Notification',
            message='This is a test notification',
            notification_type='info',
            priority='normal'
        )
    
    def test_notification_list_api(self):
        """Test notification list API endpoint."""
        url = reverse('notification-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_notification_detail_api(self):
        """Test notification detail API endpoint."""
        url = reverse('notification-detail', kwargs={'pk': self.notification.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Notification')
        self.assertEqual(response.data['message'], 'This is a test notification')
    
    def test_notification_create_api(self):
        """Test notification creation API endpoint."""
        url = reverse('notification-list')
        data = {
            'title': 'New Notification',
            'message': 'This is a new notification',
            'notification_type': 'warning',
            'priority': 'high'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Notification')
        self.assertEqual(response.data['message'], 'This is a new notification')
        
        # Verify notification was created
        self.assertTrue(Notification.objects.filter(title='New Notification').exists())
    
    def test_notification_update_api(self):
        """Test notification update API endpoint."""
        url = reverse('notification-detail', kwargs={'pk': self.notification.id})
        data = {
            'title': 'Updated Notification',
            'is_read': True
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Notification')
        self.assertTrue(response.data['is_read'])
    
    def test_notification_unread_api(self):
        """Test unread notifications API endpoint."""
        # Create an unread notification
        Notification.objects.create(
            user=self.user,
            title='Unread Notification',
            message='This is unread',
            notification_type='info',
            priority='normal',
            is_read=False
        )
        
        url = reverse('notification-unread')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_notification_mark_read_api(self):
        """Test mark notification as read API endpoint."""
        url = reverse('notification-mark-read', kwargs={'pk': self.notification.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        
        # Verify notification was marked as read
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
    
    def test_notification_mark_all_read_api(self):
        """Test mark all notifications as read API endpoint."""
        # Create multiple unread notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                title=f'Unread Notification {i}',
                message=f'This is unread {i}',
                notification_type='info',
                priority='normal',
                is_read=False
            )
        
        url = reverse('notification-mark-all-read')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('updated', response.data)
        self.assertGreater(response.data['updated'], 0)
    
    def test_notification_filtering(self):
        """Test notification filtering."""
        # Create notifications with different types
        Notification.objects.create(
            user=self.user,
            title='Warning Notification',
            message='This is a warning',
            notification_type='warning',
            priority='high'
        )
        
        url = reverse('notification-list')
        response = self.client.get(url, {'notification_type': 'warning'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_notification_search(self):
        """Test notification search."""
        url = reverse('notification-list')
        response = self.client.get(url, {'search': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class NotificationTemplateAPITestCase(APITestCase):
    """Test cases for notification template API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for template management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.template = NotificationTemplate.objects.create(
            name='test_template',
            title_template='Test: {title}',
            message_template='Message: {message}',
            notification_type='info'
        )
    
    def test_notification_template_list_api(self):
        """Test notification template list API endpoint."""
        url = reverse('notificationtemplate-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_template_detail_api(self):
        """Test notification template detail API endpoint."""
        url = reverse('notificationtemplate-detail', kwargs={'pk': self.template.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test_template')
        self.assertEqual(response.data['title_template'], 'Test: {title}')
    
    def test_notification_template_create_api(self):
        """Test notification template creation API endpoint."""
        url = reverse('notificationtemplate-list')
        data = {
            'name': 'new_template',
            'title_template': 'New: {title}',
            'message_template': 'New message: {message}',
            'notification_type': 'warning',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_template')
        self.assertEqual(response.data['notification_type'], 'warning')
    
    def test_notification_template_active_api(self):
        """Test active notification templates API endpoint."""
        url = reverse('notificationtemplate-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class NotificationChannelAPITestCase(APITestCase):
    """Test cases for notification channel API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for channel management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email',
            config='{"smtp_server": "smtp.example.com"}'
        )
    
    def test_notification_channel_list_api(self):
        """Test notification channel list API endpoint."""
        url = reverse('notificationchannel-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_channel_detail_api(self):
        """Test notification channel detail API endpoint."""
        url = reverse('notificationchannel-detail', kwargs={'pk': self.channel.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test_channel')
        self.assertEqual(response.data['channel_type'], 'email')
    
    def test_notification_channel_create_api(self):
        """Test notification channel creation API endpoint."""
        url = reverse('notificationchannel-list')
        data = {
            'name': 'new_channel',
            'channel_type': 'sms',
            'config': '{"api_key": "test_key"}',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_channel')
        self.assertEqual(response.data['channel_type'], 'sms')
    
    def test_notification_channel_active_api(self):
        """Test active notification channels API endpoint."""
        url = reverse('notificationchannel-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class NotificationSubscriptionAPITestCase(APITestCase):
    """Test cases for notification subscription API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.channel = NotificationChannel.objects.create(
            name='test_channel',
            channel_type='email'
        )
        
        self.subscription = NotificationSubscription.objects.create(
            user=self.user,
            channel=self.channel,
            notification_types=['info', 'warning'],
            is_enabled=True
        )
    
    def test_notification_subscription_list_api(self):
        """Test notification subscription list API endpoint."""
        url = reverse('notificationsubscription-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_subscription_detail_api(self):
        """Test notification subscription detail API endpoint."""
        url = reverse('notificationsubscription-detail', kwargs={'pk': self.subscription.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notification_types'], ['info', 'warning'])
        self.assertTrue(response.data['is_enabled'])
    
    def test_notification_subscription_create_api(self):
        """Test notification subscription creation API endpoint."""
        new_channel = NotificationChannel.objects.create(
            name='new_channel',
            channel_type='sms'
        )
        
        url = reverse('notificationsubscription-list')
        data = {
            'channel': new_channel.id,
            'notification_types': ['error', 'success'],
            'is_enabled': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['notification_types'], ['error', 'success'])
        self.assertTrue(response.data['is_enabled'])
    
    def test_notification_subscription_me_api(self):
        """Test current user's subscriptions API endpoint."""
        url = reverse('notificationsubscription-me')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)


class NotificationGroupAPITestCase(APITestCase):
    """Test cases for notification group API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for group management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.group = NotificationGroup.objects.create(
            name='test_group',
            description='Test notification group',
            is_active=True
        )
        self.group.users.add(self.user)
    
    def test_notification_group_list_api(self):
        """Test notification group list API endpoint."""
        url = reverse('notificationgroup-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_group_detail_api(self):
        """Test notification group detail API endpoint."""
        url = reverse('notificationgroup-detail', kwargs={'pk': self.group.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test_group')
        self.assertEqual(response.data['description'], 'Test notification group')
    
    def test_notification_group_create_api(self):
        """Test notification group creation API endpoint."""
        url = reverse('notificationgroup-list')
        data = {
            'name': 'new_group',
            'description': 'New notification group',
            'is_active': True,
            'users': [self.user.id]
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_group')
        self.assertEqual(response.data['description'], 'New notification group')


class NotificationScheduleAPITestCase(APITestCase):
    """Test cases for notification schedule API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True  # Staff user for schedule management
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.template = NotificationTemplate.objects.create(
            name='schedule_template',
            title_template='Scheduled: {title}',
            message_template='Scheduled: {message}',
            notification_type='info'
        )
        
        self.schedule = NotificationSchedule.objects.create(
            name='test_schedule',
            template=self.template,
            schedule_type='cron',
            cron_expression='0 9 * * 1-5',
            is_active=True
        )
    
    def test_notification_schedule_list_api(self):
        """Test notification schedule list API endpoint."""
        url = reverse('notificationschedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_schedule_detail_api(self):
        """Test notification schedule detail API endpoint."""
        url = reverse('notificationschedule-detail', kwargs={'pk': self.schedule.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'test_schedule')
        self.assertEqual(response.data['schedule_type'], 'cron')
        self.assertEqual(response.data['cron_expression'], '0 9 * * 1-5')
    
    def test_notification_schedule_create_api(self):
        """Test notification schedule creation API endpoint."""
        url = reverse('notificationschedule-list')
        data = {
            'name': 'new_schedule',
            'template': self.template.id,
            'schedule_type': 'interval',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'new_schedule')
        self.assertEqual(response.data['schedule_type'], 'interval')
    
    def test_notification_schedule_active_api(self):
        """Test active notification schedules API endpoint."""
        url = reverse('notificationschedule-active')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)


class NotificationDeliveryAPITestCase(APITestCase):
    """Test cases for notification delivery API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
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
        
        self.delivery = NotificationDelivery.objects.create(
            notification=self.notification,
            channel=self.channel,
            status='delivered',
            external_id='ext_123'
        )
    
    def test_notification_delivery_list_api(self):
        """Test notification delivery list API endpoint."""
        url = reverse('notificationdelivery-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_notification_delivery_detail_api(self):
        """Test notification delivery detail API endpoint."""
        url = reverse('notificationdelivery-detail', kwargs={'pk': self.delivery.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'delivered')
        self.assertEqual(response.data['external_id'], 'ext_123')
    
    def test_notification_delivery_filtering(self):
        """Test notification delivery filtering."""
        url = reverse('notificationdelivery-list')
        response = self.client.get(url, {'status': 'delivered'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
