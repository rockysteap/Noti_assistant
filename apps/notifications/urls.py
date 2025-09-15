"""
Notifications app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet)
router.register(r'templates', views.NotificationTemplateViewSet)
router.register(r'channels', views.NotificationChannelViewSet)
router.register(r'deliveries', views.NotificationDeliveryViewSet)
router.register(r'subscriptions', views.NotificationSubscriptionViewSet)
router.register(r'groups', views.NotificationGroupViewSet)
router.register(r'schedules', views.NotificationScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
