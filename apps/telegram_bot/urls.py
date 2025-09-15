"""
Telegram bot app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.TelegramUserViewSet)
router.register(r'conversations', views.BotConversationViewSet)
router.register(r'commands', views.BotCommandViewSet)
router.register(r'messages', views.BotMessageViewSet)
router.register(r'webhooks', views.BotWebhookViewSet)
router.register(r'analytics', views.BotAnalyticsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('telegram/', views.telegram_webhook, name='telegram_webhook'),
]
