"""
Tests for core app API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from apps.core.models import UserProfile, SystemSettings, AuditLog


class CoreAPITestCase(APITestCase):
    """Test cases for core API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            timezone='America/New_York',
            language='en'
        )
    
    def test_user_list_api(self):
        """Test user list API endpoint."""
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_user_detail_api(self):
        """Test user detail API endpoint."""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.user.username)
        self.assertEqual(response.data['email'], self.user.email)
    
    def test_user_create_api(self):
        """Test user creation API endpoint."""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPassword123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'newuser@example.com')
        
        # Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_update_api(self):
        """Test user update API endpoint."""
        url = reverse('user-detail', kwargs={'pk': self.user.id})
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
    
    def test_user_profile_list_api(self):
        """Test user profile list API endpoint."""
        url = reverse('userprofile-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_user_profile_detail_api(self):
        """Test user profile detail API endpoint."""
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '+1234567890')
        self.assertEqual(response.data['timezone'], 'America/New_York')
    
    def test_user_profile_update_api(self):
        """Test user profile update API endpoint."""
        url = reverse('userprofile-detail', kwargs={'pk': self.profile.id})
        data = {
            'phone_number': '+9876543210',
            'timezone': 'Europe/London',
            'language': 'es'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone_number'], '+9876543210')
        self.assertEqual(response.data['timezone'], 'Europe/London')
        self.assertEqual(response.data['language'], 'es')
    
    def test_system_settings_list_api(self):
        """Test system settings list API endpoint."""
        # Create a test setting
        SystemSettings.objects.create(
            key='test_setting',
            value='{"test": "value"}',
            description='Test setting'
        )
        
        url = reverse('systemsettings-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_system_settings_create_api(self):
        """Test system settings creation API endpoint."""
        url = reverse('systemsettings-list')
        data = {
            'key': 'new_setting',
            'value': '{"new": "value"}',
            'description': 'New setting',
            'is_active': True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['key'], 'new_setting')
        self.assertEqual(response.data['value'], '{"new": "value"}')
    
    def test_audit_log_list_api(self):
        """Test audit log list API endpoint."""
        # Create a test audit log
        AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource',
            details='{"test": "details"}',
            ip_address='192.168.1.1',
            user_agent='Test Agent'
        )
        
        url = reverse('auditlog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_audit_log_create_api(self):
        """Test audit log creation API endpoint."""
        url = reverse('auditlog-list')
        data = {
            'action': 'new_action',
            'resource': 'new_resource',
            'details': '{"new": "details"}',
            'ip_address': '10.0.0.1',
            'user_agent': 'New Agent'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['action'], 'new_action')
        self.assertEqual(response.data['resource'], 'new_resource')
    
    def test_authentication_required(self):
        """Test that authentication is required for API endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_permission_denied_for_other_users(self):
        """Test permission denied for accessing other users' data."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_profile = UserProfile.objects.create(user=other_user)
        
        # Try to access other user's profile
        url = reverse('userprofile-detail', kwargs={'pk': other_profile.id})
        response = self.client.get(url)
        
        # Should be denied (depending on permission implementation)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])


class HealthCheckAPITestCase(APITestCase):
    """Test cases for health check API endpoints."""
    
    def test_health_check_api(self):
        """Test health check API endpoint."""
        url = reverse('health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_database_health_check_api(self):
        """Test database health check API endpoint."""
        url = reverse('database-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'healthy')
    
    def test_redis_health_check_api(self):
        """Test Redis health check API endpoint."""
        url = reverse('redis-health')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'healthy')


class APIPaginationTestCase(APITestCase):
    """Test cases for API pagination."""
    
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
        for i in range(25):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
    
    def test_user_list_pagination(self):
        """Test user list pagination."""
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
    
    def test_user_list_page_size(self):
        """Test user list page size."""
        url = reverse('user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 20)  # Default page size


class APIFilteringTestCase(APITestCase):
    """Test cases for API filtering."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_user_search_by_username(self):
        """Test user search by username."""
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_user_search_by_email(self):
        """Test user search by email."""
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'test@example.com'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_user_ordering(self):
        """Test user ordering."""
        url = reverse('user-list')
        response = self.client.get(url, {'ordering': 'username'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Check if results are ordered by username
        if len(results) > 1:
            self.assertLessEqual(results[0]['username'], results[1]['username'])


class APIErrorHandlingTestCase(APITestCase):
    """Test cases for API error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
    
    def test_user_not_found(self):
        """Test user not found error."""
        url = reverse('user-detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_user_data(self):
        """Test invalid user data validation."""
        url = reverse('user-list')
        data = {
            'username': '',  # Invalid: empty username
            'email': 'invalid-email',  # Invalid: malformed email
            'password': '123'  # Invalid: too short password
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
    
    def test_duplicate_username(self):
        """Test duplicate username error."""
        url = reverse('user-list')
        data = {
            'username': 'testuser',  # Already exists
            'email': 'new@example.com',
            'password': 'NewPassword123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
