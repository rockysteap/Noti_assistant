"""
Custom validators for the Noti project.
"""

import re
import json
from datetime import datetime, timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PhoneNumberValidator:
    """
    Validator for phone numbers in international format.
    """
    message = _('Enter a valid phone number in international format (e.g., +1234567890).')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', str(value))
        
        # Check if it starts with + and has 10-15 digits
        if not re.match(r'^\+\d{10,15}$', cleaned):
            raise ValidationError(self.message)


class TimezoneValidator:
    """
    Validator for timezone strings.
    """
    message = _('Enter a valid timezone (e.g., UTC, America/New_York, Europe/London).')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(value)
        except Exception:
            raise ValidationError(self.message)


class LanguageCodeValidator:
    """
    Validator for language codes (ISO 639-1).
    """
    message = _('Enter a valid language code (e.g., en, es, fr, de).')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        # Check if it's a valid 2-letter language code
        if not re.match(r'^[a-z]{2}$', str(value).lower()):
            raise ValidationError(self.message)


class JSONFieldValidator:
    """
    Validator for JSON fields.
    """
    message = _('Enter valid JSON data.')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        if isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(self.message)
        elif not isinstance(value, (dict, list)):
            raise ValidationError(self.message)


class CronExpressionValidator:
    """
    Validator for cron expressions.
    """
    message = _('Enter a valid cron expression (e.g., "0 9 * * 1-5" for weekdays at 9 AM).')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        # Basic cron expression validation
        parts = str(value).strip().split()
        if len(parts) != 5:
            raise ValidationError(self.message)
        
        # Validate each part
        for i, part in enumerate(parts):
            if not self._validate_cron_part(part, i):
                raise ValidationError(self.message)
    
    def _validate_cron_part(self, part, index):
        """Validate a single cron expression part."""
        if part == '*':
            return True
        
        # Handle ranges and lists
        if ',' in part:
            return all(self._validate_cron_part(p.strip(), index) for p in part.split(','))
        
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                return (self._validate_cron_part(start, index) and 
                       self._validate_cron_part(end, index))
            except ValueError:
                return False
        
        # Handle step values
        if '/' in part:
            try:
                value, step = part.split('/', 1)
                return (self._validate_cron_part(value, index) and 
                       step.isdigit() and int(step) > 0)
            except ValueError:
                return False
        
        # Validate numeric values
        try:
            num = int(part)
            if index == 0:  # minute
                return 0 <= num <= 59
            elif index == 1:  # hour
                return 0 <= num <= 23
            elif index == 2:  # day
                return 1 <= num <= 31
            elif index == 3:  # month
                return 1 <= num <= 12
            elif index == 4:  # weekday
                return 0 <= num <= 6
        except ValueError:
            return False
        
        return True


class FutureDateTimeValidator:
    """
    Validator to ensure datetime is in the future.
    """
    message = _('Date and time must be in the future.')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError(_('Enter a valid datetime format.'))
        
        if value <= datetime.now(timezone.utc):
            raise ValidationError(self.message)


class URLValidator:
    """
    Enhanced URL validator with additional checks.
    """
    message = _('Enter a valid URL.')
    
    def __init__(self, message=None, allowed_schemes=None):
        if message:
            self.message = message
        self.allowed_schemes = allowed_schemes or ['http', 'https']
    
    def __call__(self, value):
        if not value:
            return
        
        from django.core.validators import URLValidator as DjangoURLValidator
        
        try:
            validator = DjangoURLValidator(schemes=self.allowed_schemes)
            validator(value)
        except ValidationError:
            raise ValidationError(self.message)


class TelegramUsernameValidator:
    """
    Validator for Telegram usernames.
    """
    message = _('Enter a valid Telegram username (5-32 characters, letters, numbers, underscores only).')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        username = str(value).strip()
        
        # Check length
        if not (5 <= len(username) <= 32):
            raise ValidationError(self.message)
        
        # Check format (letters, numbers, underscores only)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError(self.message)
        
        # Cannot start or end with underscore
        if username.startswith('_') or username.endswith('_'):
            raise ValidationError(self.message)


class NotificationTypeValidator:
    """
    Validator for notification types.
    """
    VALID_TYPES = [
        'info', 'warning', 'error', 'success', 'urgent',
        'email', 'sms', 'push', 'telegram', 'webhook'
    ]
    message = _('Enter a valid notification type. Valid types: {valid_types}').format(
        valid_types=', '.join(VALID_TYPES)
    )
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        if str(value).lower() not in self.VALID_TYPES:
            raise ValidationError(self.message)


class PriorityValidator:
    """
    Validator for priority levels.
    """
    VALID_PRIORITIES = ['low', 'normal', 'high', 'urgent', 'critical']
    message = _('Enter a valid priority level. Valid priorities: {valid_priorities}').format(
        valid_priorities=', '.join(VALID_PRIORITIES)
    )
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        if str(value).lower() not in self.VALID_PRIORITIES:
            raise ValidationError(self.message)


class ChannelTypeValidator:
    """
    Validator for notification channel types.
    """
    VALID_TYPES = ['email', 'sms', 'push', 'telegram', 'webhook', 'slack', 'discord']
    message = _('Enter a valid channel type. Valid types: {valid_types}').format(
        valid_types=', '.join(VALID_TYPES)
    )
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        if str(value).lower() not in self.VALID_TYPES:
            raise ValidationError(self.message)


class EmailValidator:
    """
    Enhanced email validator.
    """
    message = _('Enter a valid email address.')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        from django.core.validators import validate_email
        try:
            validate_email(value)
        except ValidationError:
            raise ValidationError(self.message)


class PasswordStrengthValidator:
    """
    Validator for password strength.
    """
    message = _('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.')
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not value:
            return
        
        password = str(value)
        
        # Check length
        if len(password) < 8:
            raise ValidationError(self.message)
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError(self.message)
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError(self.message)
        
        # Check for number
        if not re.search(r'\d', password):
            raise ValidationError(self.message)


class CustomValidationMixin:
    """
    Mixin for custom validation methods in serializers.
    """
    
    def validate_metadata(self, value):
        """Validate metadata JSON field."""
        if value and isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Metadata must be valid JSON.")
        return value
    
    def validate_config(self, value):
        """Validate config JSON field."""
        if value and isinstance(value, str):
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError("Config must be valid JSON.")
        return value
    
    def validate_scheduled_at(self, value):
        """Validate scheduled_at is in the future."""
        if value and value <= datetime.now(timezone.utc):
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value
    
    def validate_expires_at(self, value):
        """Validate expires_at is in the future."""
        if value and value <= datetime.now(timezone.utc):
            raise serializers.ValidationError("Expiration time must be in the future.")
        return value
    
    def validate_webhook_url(self, value):
        """Validate webhook URL."""
        if value:
            from django.core.validators import URLValidator
            validator = URLValidator(schemes=['http', 'https'])
            try:
                validator(value)
            except ValidationError:
                raise serializers.ValidationError("Enter a valid webhook URL.")
        return value
