"""
Core app serializers.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, SystemSettings, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    """
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'phone_number', 'timezone', 'language', 'is_verified', 'created_at', 'updated_at']


class SystemSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for SystemSettings model.
    """
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model.
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'resource', 'details', 'ip_address', 'user_agent', 'created_at']
        read_only_fields = ['id', 'date_joined']
