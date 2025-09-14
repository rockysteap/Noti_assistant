"""
Notifications app serializers.
"""

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    
    class Meta:
        model = Notification
        fields = '__all__'
