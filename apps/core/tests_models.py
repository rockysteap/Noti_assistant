"""
Tests for core app models.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.core.models import UserProfile, SystemSettings, AuditLog


class UserProfileModelTestCase(TestCase):
    """Test cases for UserProfile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test UserProfile creation."""
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890',
            timezone='America/New_York',
            language='en',
            is_verified=True
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.timezone, 'America/New_York')
        self.assertEqual(profile.language, 'en')
        self.assertTrue(profile.is_verified)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
    
    def test_user_profile_str(self):
        """Test UserProfile string representation."""
        profile = UserProfile.objects.create(user=self.user)
        expected = f"{self.user.username} Profile"
        self.assertEqual(str(profile), expected)
    
    def test_user_profile_one_to_one_relationship(self):
        """Test one-to-one relationship with User."""
        profile = UserProfile.objects.create(user=self.user)
        
        # Test reverse relationship
        self.assertEqual(self.user.profile, profile)
        
        # Test that only one profile can exist per user
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=self.user)
    
    def test_user_profile_default_values(self):
        """Test UserProfile default values."""
        profile = UserProfile.objects.create(user=self.user)
        
        self.assertEqual(profile.phone_number, '')
        self.assertEqual(profile.timezone, 'UTC')
        self.assertEqual(profile.language, 'en')
        self.assertFalse(profile.is_verified)


class SystemSettingsModelTestCase(TestCase):
    """Test cases for SystemSettings model."""
    
    def test_system_settings_creation(self):
        """Test SystemSettings creation."""
        setting = SystemSettings.objects.create(
            key='test_setting',
            value='{"test": "value"}',
            description='Test setting',
            is_active=True
        )
        
        self.assertEqual(setting.key, 'test_setting')
        self.assertEqual(setting.value, '{"test": "value"}')
        self.assertEqual(setting.description, 'Test setting')
        self.assertTrue(setting.is_active)
        self.assertIsNotNone(setting.created_at)
        self.assertIsNotNone(setting.updated_at)
    
    def test_system_settings_str(self):
        """Test SystemSettings string representation."""
        setting = SystemSettings.objects.create(
            key='test_setting',
            value='test_value',
            description='Test setting'
        )
        expected = 'test_setting: test_value'
        self.assertEqual(str(setting), expected)
    
    def test_system_settings_unique_key(self):
        """Test SystemSettings unique key constraint."""
        SystemSettings.objects.create(
            key='unique_setting',
            value='value1',
            description='First setting'
        )
        
        # Try to create another setting with the same key
        with self.assertRaises(Exception):
            SystemSettings.objects.create(
                key='unique_setting',
                value='value2',
                description='Second setting'
            )
    
    def test_system_settings_default_values(self):
        """Test SystemSettings default values."""
        setting = SystemSettings.objects.create(
            key='default_test',
            value='test_value'
        )
        
        self.assertEqual(setting.description, '')
        self.assertTrue(setting.is_active)


class AuditLogModelTestCase(TestCase):
    """Test cases for AuditLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_audit_log_creation(self):
        """Test AuditLog creation."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource',
            details='{"test": "details"}',
            ip_address='192.168.1.1',
            user_agent='Test Agent'
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'test_action')
        self.assertEqual(audit_log.resource, 'test_resource')
        self.assertEqual(audit_log.details, '{"test": "details"}')
        self.assertEqual(audit_log.ip_address, '192.168.1.1')
        self.assertEqual(audit_log.user_agent, 'Test Agent')
        self.assertIsNotNone(audit_log.created_at)
    
    def test_audit_log_str(self):
        """Test AuditLog string representation."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource'
        )
        expected = f"{self.user.username} - test_action - test_resource"
        self.assertEqual(str(audit_log), expected)
    
    def test_audit_log_optional_fields(self):
        """Test AuditLog with optional fields."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource'
        )
        
        self.assertEqual(audit_log.details, {})
        self.assertIsNone(audit_log.ip_address)
        self.assertEqual(audit_log.user_agent, '')
    
    def test_audit_log_ordering(self):
        """Test AuditLog ordering by created_at."""
        # Create multiple audit logs
        log1 = AuditLog.objects.create(
            user=self.user,
            action='action1',
            resource='resource1'
        )
        log2 = AuditLog.objects.create(
            user=self.user,
            action='action2',
            resource='resource2'
        )
        
        # Get all logs
        logs = AuditLog.objects.all()
        
        # Should be ordered by created_at descending (newest first)
        self.assertEqual(logs[0], log2)
        self.assertEqual(logs[1], log1)


class ModelRelationshipsTestCase(TestCase):
    """Test cases for model relationships."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(user=self.user)
    
    def test_user_profile_relationship(self):
        """Test User-UserProfile relationship."""
        # Test forward relationship
        self.assertEqual(self.profile.user, self.user)
        
        # Test reverse relationship
        self.assertEqual(self.user.profile, self.profile)
    
    def test_user_audit_log_relationship(self):
        """Test User-AuditLog relationship."""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource'
        )
        
        # Test forward relationship
        self.assertEqual(audit_log.user, self.user)
        
        # Test reverse relationship
        self.assertIn(audit_log, self.user.auditlog_set.all())
    
    def test_cascade_deletion(self):
        """Test cascade deletion behavior."""
        # Create audit log
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource'
        )
        
        # Delete user
        self.user.delete()
        
        # Profile should be deleted (CASCADE)
        self.assertFalse(UserProfile.objects.filter(id=self.profile.id).exists())
        
        # Audit log should NOT be deleted (SET_NULL)
        self.assertTrue(AuditLog.objects.filter(id=audit_log.id).exists())


class ModelValidationTestCase(TestCase):
    """Test cases for model validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_phone_number_validation(self):
        """Test UserProfile phone number validation."""
        # This would test custom validation if implemented
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number='+1234567890'
        )
        self.assertEqual(profile.phone_number, '+1234567890')
    
    def test_system_settings_json_validation(self):
        """Test SystemSettings JSON validation."""
        # Valid JSON
        setting = SystemSettings.objects.create(
            key='valid_json',
            value='{"key": "value"}'
        )
        self.assertEqual(setting.value, '{"key": "value"}')
        
        # Invalid JSON (should still be stored as string)
        setting = SystemSettings.objects.create(
            key='invalid_json',
            value='invalid json string'
        )
        self.assertEqual(setting.value, 'invalid json string')
    
    def test_audit_log_details_json_validation(self):
        """Test AuditLog details JSON validation."""
        # Valid JSON
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource',
            details='{"key": "value"}'
        )
        self.assertEqual(audit_log.details, '{"key": "value"}')
        
        # Empty JSON
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='test_action',
            resource='test_resource'
        )
        self.assertEqual(audit_log.details, {})
