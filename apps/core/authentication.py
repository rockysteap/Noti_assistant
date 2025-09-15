"""
Custom authentication classes for the Noti project.
"""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import User
from django.conf import settings
import hashlib
import hmac
import json
from .models import TelegramUser


class TelegramAuthentication(BaseAuthentication):
    """
    Custom authentication for Telegram users.
    Authenticates users based on Telegram data and hash verification.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using Telegram data.
        """
        # Get Telegram data from headers or request data
        telegram_data = self._get_telegram_data(request)
        if not telegram_data:
            return None
        
        # Verify the hash
        if not self._verify_telegram_hash(telegram_data):
            raise AuthenticationFailed('Invalid Telegram hash')
        
        # Get or create user
        user = self._get_or_create_user(telegram_data)
        if not user:
            raise AuthenticationFailed('Unable to create or retrieve user')
        
        return (user, None)
    
    def _get_telegram_data(self, request):
        """
        Extract Telegram data from request headers or body.
        """
        # Try to get from headers first
        telegram_data = request.META.get('HTTP_X_TELEGRAM_DATA')
        if telegram_data:
            try:
                return json.loads(telegram_data)
            except json.JSONDecodeError:
                pass
        
        # Try to get from request body
        if hasattr(request, 'data') and 'telegram_data' in request.data:
            return request.data['telegram_data']
        
        return None
    
    def _verify_telegram_hash(self, telegram_data):
        """
        Verify the Telegram hash to ensure data integrity.
        """
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            return False
        
        # Extract hash from data
        received_hash = telegram_data.pop('hash', None)
        if not received_hash:
            return False
        
        # Create data string for verification
        data_check_string = '\n'.join([
            f"{key}={value}" for key, value in sorted(telegram_data.items())
        ])
        
        # Create secret key
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(received_hash, calculated_hash)
    
    def _get_or_create_user(self, telegram_data):
        """
        Get or create a user based on Telegram data.
        """
        telegram_id = telegram_data.get('id')
        if not telegram_id:
            return None
        
        try:
            # Try to get existing Telegram user
            telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
            return telegram_user.user
        except TelegramUser.DoesNotExist:
            # Create new user and Telegram user
            username = telegram_data.get('username', f'telegram_{telegram_id}')
            first_name = telegram_data.get('first_name', '')
            last_name = telegram_data.get('last_name', '')
            
            # Create Django user
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=telegram_data.get('email', ''),
            )
            
            # Create Telegram user
            TelegramUser.objects.create(
                user=user,
                telegram_id=telegram_id,
                username=telegram_data.get('username', ''),
                first_name=first_name,
                last_name=last_name,
                language_code=telegram_data.get('language_code', 'en'),
                is_bot=telegram_data.get('is_bot', False),
                is_premium=telegram_data.get('is_premium', False),
            )
            
            return user


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication using API keys.
    """
    
    def authenticate(self, request):
        """
        Authenticate using API key from headers.
        """
        api_key = request.META.get('HTTP_X_API_KEY')
        if not api_key:
            return None
        
        # In a real implementation, you would check against a database
        # For now, we'll use a simple check against settings
        valid_api_key = getattr(settings, 'API_KEY', None)
        if not valid_api_key or api_key != valid_api_key:
            raise AuthenticationFailed('Invalid API key')
        
        # Return a system user or create a special API user
        try:
            user = User.objects.get(username='api_user')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='api_user',
                email='api@noti.local',
                is_active=True
            )
        
        return (user, None)
