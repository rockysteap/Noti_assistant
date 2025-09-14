"""
Health check URLs.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('db/', views.database_health, name='database_health'),
    path('redis/', views.redis_health, name='redis_health'),
]
