"""
Core app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile, SystemSettings, AuditLog
from .validators import (
    PhoneNumberValidator, TimezoneValidator, LanguageCodeValidator,
    JSONFieldValidator, EmailValidator, PasswordStrengthValidator,
    CustomValidationMixin
)


class UserSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for User model with enhanced validation.
    """
    email = serializers.EmailField(validators=[EmailValidator()])
    password = serializers.CharField(write_only=True, validators=[PasswordStrengthValidator()])
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_active', 'date_joined']
        extra_kwargs = {
            'username': {'min_length': 3, 'max_length': 150},
            'first_name': {'max_length': 150},
            'last_name': {'max_length': 150},
        }
    
    def validate_username(self, value):
        """Validate username uniqueness and format."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Username can only contain letters, numbers, underscores, and hyphens.")
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password."""
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with password handling."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user


class UserProfileSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for UserProfile model with enhanced validation.
    """
    user = UserSerializer(read_only=True)
    phone_number = serializers.CharField(
        required=False, 
        allow_blank=True, 
        validators=[PhoneNumberValidator()]
    )
    timezone = serializers.CharField(
        required=False, 
        allow_blank=True, 
        validators=[TimezoneValidator()]
    )
    language = serializers.CharField(
        required=False, 
        allow_blank=True, 
        validators=[LanguageCodeValidator()]
    )
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'phone_number', 'timezone', 'language', 'is_verified', 'created_at', 'updated_at']
        extra_kwargs = {
            'phone_number': {'max_length': 20},
            'timezone': {'max_length': 50},
            'language': {'max_length': 10},
        }
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code (e.g., +1234567890).")
        return value


class SystemSettingsSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for SystemSettings model with enhanced validation.
    """
    value = serializers.CharField(validators=[JSONFieldValidator()])
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']
        extra_kwargs = {
            'key': {'max_length': 100},
            'description': {'max_length': 500},
        }
    
    def validate_key(self, value):
        """Validate setting key format."""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Key can only contain letters, numbers, underscores, and hyphens.")
        return value


class AuditLogSerializer(serializers.ModelSerializer, CustomValidationMixin):
    """
    Serializer for AuditLog model with enhanced validation.
    """
    user = UserSerializer(read_only=True)
    details = serializers.CharField(validators=[JSONFieldValidator()])
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'resource', 'details', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'action': {'max_length': 100},
            'resource': {'max_length': 200},
            'ip_address': {'max_length': 45},  # IPv6 max length
            'user_agent': {'max_length': 500},
        }
    
    def validate_action(self, value):
        """Validate action format."""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError("Action can only contain letters, numbers, underscores, and hyphens.")
        return value
