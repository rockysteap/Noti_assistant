"""
Tests for validation and error handling functionality.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from apps.core.validators import (
    PhoneNumberValidator, TimezoneValidator, LanguageCodeValidator,
    JSONFieldValidator, CronExpressionValidator, FutureDateTimeValidator,
    TelegramUsernameValidator, NotificationTypeValidator, PriorityValidator,
    ChannelTypeValidator, EmailValidator, PasswordStrengthValidator
)
from apps.core.serializers import UserSerializer, UserProfileSerializer
from apps.core.exceptions import (
    ValidationError as NotiValidationError, AuthenticationError,
    PermissionError, NotFoundError, ConflictError, RateLimitError
)
from datetime import datetime, timezone, timedelta


class ValidatorTestCase(TestCase):
    """Test cases for custom validators."""
    
    def test_phone_number_validator(self):
        """Test phone number validation."""
        validator = PhoneNumberValidator()
        
        # Valid phone numbers
        valid_numbers = ['+1234567890', '+44123456789', '+33123456789']
        for number in valid_numbers:
            try:
                validator(number)
            except ValidationError:
                self.fail(f"Phone number {number} should be valid")
        
        # Invalid phone numbers
        invalid_numbers = ['1234567890', '+123', '+12345678901234567890', 'abc']
        for number in invalid_numbers:
            with self.assertRaises(ValidationError):
                validator(number)
    
    def test_timezone_validator(self):
        """Test timezone validation."""
        validator = TimezoneValidator()
        
        # Valid timezones
        valid_timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo']
        for tz in valid_timezones:
            try:
                validator(tz)
            except ValidationError:
                self.fail(f"Timezone {tz} should be valid")
        
        # Invalid timezones
        invalid_timezones = ['Invalid/Timezone', 'EST', 'PST']
        for tz in invalid_timezones:
            with self.assertRaises(ValidationError):
                validator(tz)
    
    def test_language_code_validator(self):
        """Test language code validation."""
        validator = LanguageCodeValidator()
        
        # Valid language codes
        valid_codes = ['en', 'es', 'fr', 'de', 'zh', 'ja']
        for code in valid_codes:
            try:
                validator(code)
            except ValidationError:
                self.fail(f"Language code {code} should be valid")
        
        # Invalid language codes
        invalid_codes = ['eng', 'english', 'EN', 'e', '123']
        for code in invalid_codes:
            with self.assertRaises(ValidationError):
                validator(code)
    
    def test_json_field_validator(self):
        """Test JSON field validation."""
        validator = JSONFieldValidator()
        
        # Valid JSON
        valid_json = ['{"key": "value"}', '{"array": [1, 2, 3]}', '[]', '{}']
        for json_str in valid_json:
            try:
                validator(json_str)
            except ValidationError:
                self.fail(f"JSON {json_str} should be valid")
        
        # Valid dict/list
        valid_objects = [{'key': 'value'}, [1, 2, 3], {}]
        for obj in valid_objects:
            try:
                validator(obj)
            except ValidationError:
                self.fail(f"Object {obj} should be valid")
        
        # Invalid JSON
        invalid_json = ['{"key": "value"', 'invalid json', '{"key": }']
        for json_str in invalid_json:
            with self.assertRaises(ValidationError):
                validator(json_str)
    
    def test_cron_expression_validator(self):
        """Test cron expression validation."""
        validator = CronExpressionValidator()
        
        # Valid cron expressions
        valid_crons = [
            '0 9 * * 1-5',  # Weekdays at 9 AM
            '*/15 * * * *',  # Every 15 minutes
            '0 0 1 * *',     # First day of month
            '0 12 * * 0',    # Sundays at noon
            '30 2 * * 1-5'   # Weekdays at 2:30 AM
        ]
        for cron in valid_crons:
            try:
                validator(cron)
            except ValidationError:
                self.fail(f"Cron expression {cron} should be valid")
        
        # Invalid cron expressions
        invalid_crons = [
            '0 9 * *',       # Missing weekday
            '60 9 * * 1-5',  # Invalid minute
            '0 25 * * 1-5',  # Invalid hour
            '0 9 32 * 1-5',  # Invalid day
            '0 9 * 13 1-5',  # Invalid month
            '0 9 * * 8',     # Invalid weekday
            'invalid cron'   # Not a cron expression
        ]
        for cron in invalid_crons:
            with self.assertRaises(ValidationError):
                validator(cron)
    
    def test_future_datetime_validator(self):
        """Test future datetime validation."""
        validator = FutureDateTimeValidator()
        
        # Future datetime
        future_dt = datetime.now(timezone.utc) + timedelta(hours=1)
        try:
            validator(future_dt)
        except ValidationError:
            self.fail("Future datetime should be valid")
        
        # Past datetime
        past_dt = datetime.now(timezone.utc) - timedelta(hours=1)
        with self.assertRaises(ValidationError):
            validator(past_dt)
    
    def test_telegram_username_validator(self):
        """Test Telegram username validation."""
        validator = TelegramUsernameValidator()
        
        # Valid usernames
        valid_usernames = ['username', 'user_name', 'user123', 'test_user_123']
        for username in valid_usernames:
            try:
                validator(username)
            except ValidationError:
                self.fail(f"Username {username} should be valid")
        
        # Invalid usernames
        invalid_usernames = [
            'user',           # Too short
            'a' * 33,         # Too long
            '_username',      # Starts with underscore
            'username_',      # Ends with underscore
            'user-name',      # Contains hyphen
            'user name',      # Contains space
            'user@name'       # Contains special character
        ]
        for username in invalid_usernames:
            with self.assertRaises(ValidationError):
                validator(username)
    
    def test_notification_type_validator(self):
        """Test notification type validation."""
        validator = NotificationTypeValidator()
        
        # Valid types
        valid_types = ['info', 'warning', 'error', 'success', 'urgent', 'email', 'sms']
        for notif_type in valid_types:
            try:
                validator(notif_type)
            except ValidationError:
                self.fail(f"Notification type {notif_type} should be valid")
        
        # Invalid types
        invalid_types = ['invalid', 'INFO', 'notification', 'alert']
        for notif_type in invalid_types:
            with self.assertRaises(ValidationError):
                validator(notif_type)
    
    def test_priority_validator(self):
        """Test priority validation."""
        validator = PriorityValidator()
        
        # Valid priorities
        valid_priorities = ['low', 'normal', 'high', 'urgent', 'critical']
        for priority in valid_priorities:
            try:
                validator(priority)
            except ValidationError:
                self.fail(f"Priority {priority} should be valid")
        
        # Invalid priorities
        invalid_priorities = ['LOW', 'medium', 'top', '1', 'highest']
        for priority in invalid_priorities:
            with self.assertRaises(ValidationError):
                validator(priority)
    
    def test_channel_type_validator(self):
        """Test channel type validation."""
        validator = ChannelTypeValidator()
        
        # Valid types
        valid_types = ['email', 'sms', 'push', 'telegram', 'webhook', 'slack', 'discord']
        for channel_type in valid_types:
            try:
                validator(channel_type)
            except ValidationError:
                self.fail(f"Channel type {channel_type} should be valid")
        
        # Invalid types
        invalid_types = ['EMAIL', 'notification', 'api', 'http']
        for channel_type in invalid_types:
            with self.assertRaises(ValidationError):
                validator(channel_type)
    
    def test_email_validator(self):
        """Test email validation."""
        validator = EmailValidator()
        
        # Valid emails
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'test123@test-domain.com'
        ]
        for email in valid_emails:
            try:
                validator(email)
            except ValidationError:
                self.fail(f"Email {email} should be valid")
        
        # Invalid emails
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'test@',
            'test..test@example.com',
            'test@.com'
        ]
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                validator(email)
    
    def test_password_strength_validator(self):
        """Test password strength validation."""
        validator = PasswordStrengthValidator()
        
        # Valid passwords
        valid_passwords = [
            'Password123',
            'MyStr0ng!Pass',
            'Test1234',
            'ComplexP@ssw0rd'
        ]
        for password in valid_passwords:
            try:
                validator(password)
            except ValidationError:
                self.fail(f"Password {password} should be valid")
        
        # Invalid passwords
        invalid_passwords = [
            'password',      # No uppercase, no number
            'PASSWORD',      # No lowercase, no number
            'Password',      # No number
            '12345678',      # No letters
            'Pass1',         # Too short
            'password123'    # No uppercase
        ]
        for password in invalid_passwords:
            with self.assertRaises(ValidationError):
                validator(password)


class SerializerValidationTestCase(APITestCase):
    """Test cases for serializer validation."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_serializer_validation(self):
        """Test user serializer validation."""
        # Valid data
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid username
        invalid_data = self.user_data.copy()
        invalid_data['username'] = 'ab'  # Too short
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        
        # Invalid email
        invalid_data = self.user_data.copy()
        invalid_data['email'] = 'invalid-email'
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        
        # Weak password
        invalid_data = self.user_data.copy()
        invalid_data['password'] = 'weak'
        serializer = UserSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_user_profile_serializer_validation(self):
        """Test user profile serializer validation."""
        user = User.objects.create_user(**self.user_data)
        profile_data = {
            'user': user.id,
            'phone_number': '+1234567890',
            'timezone': 'America/New_York',
            'language': 'en'
        }
        
        # Valid data
        serializer = UserProfileSerializer(data=profile_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid phone number
        invalid_data = profile_data.copy()
        invalid_data['phone_number'] = '1234567890'  # Missing country code
        serializer = UserProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
        
        # Invalid timezone
        invalid_data = profile_data.copy()
        invalid_data['timezone'] = 'Invalid/Timezone'
        serializer = UserProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('timezone', serializer.errors)
        
        # Invalid language code
        invalid_data = profile_data.copy()
        invalid_data['language'] = 'english'
        serializer = UserProfileSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('language', serializer.errors)


class ExceptionTestCase(TestCase):
    """Test cases for custom exceptions."""
    
    def test_validation_error(self):
        """Test validation error exception."""
        error = NotiValidationError("Test validation error", field_errors={'field': ['Error message']})
        self.assertEqual(error.status_code, 400)
        self.assertEqual(str(error.detail), "Test validation error")
        self.assertEqual(error.field_errors, {'field': ['Error message']})
    
    def test_authentication_error(self):
        """Test authentication error exception."""
        error = AuthenticationError("Authentication failed")
        self.assertEqual(error.status_code, 401)
        self.assertEqual(str(error.detail), "Authentication failed")
    
    def test_permission_error(self):
        """Test permission error exception."""
        error = PermissionError("Permission denied")
        self.assertEqual(error.status_code, 403)
        self.assertEqual(str(error.detail), "Permission denied")
    
    def test_not_found_error(self):
        """Test not found error exception."""
        error = NotFoundError("Resource not found")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(str(error.detail), "Resource not found")
    
    def test_conflict_error(self):
        """Test conflict error exception."""
        error = ConflictError("Resource conflict")
        self.assertEqual(error.status_code, 409)
        self.assertEqual(str(error.detail), "Resource conflict")
    
    def test_rate_limit_error(self):
        """Test rate limit error exception."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        self.assertEqual(error.status_code, 429)
        self.assertEqual(str(error.detail), "Rate limit exceeded")
        self.assertEqual(error.retry_after, 60)
