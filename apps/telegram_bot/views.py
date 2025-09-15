"""
Telegram bot app views.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core.permissions import IsTelegramBotOwner, IsAdminOrOwner
import json
from .bot import handle_telegram_update
from .models import (
    TelegramUser, BotConversation, BotCommand, BotMessage, 
    BotWebhook, BotAnalytics
)
from .serializers import (
    TelegramUserSerializer, BotConversationSerializer, BotCommandSerializer,
    BotMessageSerializer, BotWebhookSerializer, BotAnalyticsSerializer
)


class TelegramUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Telegram users.
    """
    queryset = TelegramUser.objects.all()
    serializer_class = TelegramUserSerializer
    permission_classes = [IsAdminOrOwner]
    filterset_fields = ['is_verified', 'is_premium', 'is_bot']
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


class BotConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bot conversations.
    """
    queryset = BotConversation.objects.all()
    serializer_class = BotConversationSerializer
    permission_classes = [IsTelegramBotOwner]
    filterset_fields = ['state', 'user']
    ordering_fields = ['last_activity', 'created_at']
    ordering = ['-last_activity']


class BotCommandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bot commands.
    """
    queryset = BotCommand.objects.all()
    serializer_class = BotCommandSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['is_active', 'requires_auth', 'admin_only']
    search_fields = ['command', 'description']
    ordering = ['command']

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get all active bot commands.
        """
        commands = BotCommand.objects.filter(is_active=True)
        serializer = self.get_serializer(commands, many=True)
        return Response(serializer.data)


class BotMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing bot messages.
    """
    queryset = BotMessage.objects.all()
    serializer_class = BotMessageSerializer
    permission_classes = [IsTelegramBotOwner]
    filterset_fields = ['message_type', 'is_bot_message', 'user']
    search_fields = ['content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class BotWebhookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing bot webhooks.
    """
    queryset = BotWebhook.objects.all()
    serializer_class = BotWebhookSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['is_active']
    ordering = ['-created_at']


class BotAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing bot analytics.
    """
    queryset = BotAnalytics.objects.all()
    serializer_class = BotAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['date']
    ordering_fields = ['date']
    ordering = ['-date']


@csrf_exempt
@require_POST
def telegram_webhook(request):
    """
    Telegram webhook endpoint with security measures.
    """
    # 1. Verify the request is from Telegram
    secret_token = request.META.get('HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN')
    if not verify_telegram_secret(secret_token):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # 2. Rate limiting (optional)
    if is_rate_limited(request.META.get('REMOTE_ADDR')):
        return JsonResponse({'error': 'Rate limited'}, status=429)
    
    # 3. Process the webhook
    try:
        update_data = json.loads(request.body)
        handle_telegram_update(update_data)
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
