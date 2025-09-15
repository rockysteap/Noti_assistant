"""
Core app URLs.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'settings', views.SystemSettingsViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    
    # Authentication endpoints
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/register/', auth_views.register_view, name='register'),
    path('auth/change-password/', auth_views.change_password_view, name='change_password'),
    path('auth/telegram/', auth_views.telegram_auth_view, name='telegram_auth'),
    path('auth/user-info/', auth_views.user_info_view, name='user_info'),
]
