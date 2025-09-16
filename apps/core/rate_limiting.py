"""
Redis-based rate limiting implementation for the Noti project.
"""

import time
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.conf import settings
from rest_framework.throttling import BaseThrottle
from rest_framework.response import Response
from rest_framework import status


class RedisRateLimiter:
    """
    Redis-based rate limiter with sliding window algorithm.
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client or cache.client.get_client()
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int, 
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique key for rate limiting (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            identifier: Optional identifier for logging
            
        Returns:
            Dict with 'allowed', 'remaining', 'reset_time', 'retry_after'
        """
        now = int(time.time())
        window_start = now - window
        
        # Create Redis key with window
        redis_key = f"rate_limit:{key}:{window_start // window}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(now): now})
        
        # Set expiration
        pipe.expire(redis_key, window)
        
        results = pipe.execute()
        current_count = results[1]
        
        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1) if allowed else 0
        reset_time = window_start + window
        
        return {
            'allowed': allowed,
            'remaining': remaining,
            'reset_time': reset_time,
            'retry_after': reset_time - now if not allowed else 0,
            'limit': limit,
            'window': window,
            'identifier': identifier
        }


class RedisThrottle(BaseThrottle):
    """
    Redis-based throttle for Django REST Framework.
    """
    
    def __init__(self, rate: str, scope: str = None):
        """
        Initialize throttle with rate limit.
        
        Args:
            rate: Rate limit in format "number/period" (e.g., "100/hour")
            scope: Optional scope for different rate limits
        """
        self.rate = rate
        self.scope = scope
        self.limiter = RedisRateLimiter()
        
        # Parse rate limit
        self.limit, self.period = self._parse_rate(rate)
        self.window = self._get_window_seconds(self.period)
    
    def _parse_rate(self, rate: str) -> tuple:
        """Parse rate string into limit and period."""
        if '/' not in rate:
            raise ValueError("Rate must be in format 'number/period'")
        
        limit, period = rate.split('/')
        return int(limit), period
    
    def _get_window_seconds(self, period: str) -> int:
        """Convert period to seconds."""
        period_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
            'week': 604800,
        }
        
        if period not in period_map:
            raise ValueError(f"Invalid period: {period}")
        
        return period_map[period]
    
    def get_cache_key(self, request, view) -> str:
        """Generate cache key for rate limiting."""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        else:
            return f"ip:{self.get_ident(request)}"
    
    def throttle_failure(self, request, view, result: Dict[str, Any]) -> bool:
        """Handle throttle failure."""
        return not result['allowed']
    
    def throttle_success(self, request, view, result: Dict[str, Any]) -> bool:
        """Handle throttle success."""
        return result['allowed']
    
    def allow_request(self, request, view) -> bool:
        """Check if request should be allowed."""
        cache_key = self.get_cache_key(request, view)
        
        result = self.limiter.is_allowed(
            key=cache_key,
            limit=self.limit,
            window=self.window,
            identifier=getattr(request.user, 'username', 'anonymous')
        )
        
        # Store result for use in throttle_failure
        self.throttle_result = result
        
        return result['allowed']
    
    def wait(self) -> Optional[int]:
        """Return seconds to wait before next request."""
        if hasattr(self, 'throttle_result'):
            return self.throttle_result.get('retry_after', 0)
        return None


class UserRateThrottle(RedisThrottle):
    """Rate limiting for authenticated users."""
    
    def __init__(self):
        super().__init__(rate=getattr(settings, 'USER_RATE_LIMIT', '1000/hour'))
    
    def get_cache_key(self, request, view) -> str:
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        return f"ip:{self.get_ident(request)}"


class AnonRateThrottle(RedisThrottle):
    """Rate limiting for anonymous users."""
    
    def __init__(self):
        super().__init__(rate=getattr(settings, 'ANON_RATE_LIMIT', '100/hour'))
    
    def get_cache_key(self, request, view) -> str:
        return f"ip:{self.get_ident(request)}"


class APIEndpointThrottle(RedisThrottle):
    """Rate limiting for specific API endpoints."""
    
    def __init__(self, rate: str = "200/hour"):
        super().__init__(rate=rate)
    
    def get_cache_key(self, request, view) -> str:
        # Include endpoint in the key
        endpoint = f"{request.method}:{request.path}"
        if request.user.is_authenticated:
            return f"endpoint:{endpoint}:user:{request.user.id}"
        return f"endpoint:{endpoint}:ip:{self.get_ident(request)}"


class NotificationThrottle(RedisThrottle):
    """Special rate limiting for notification endpoints."""
    
    def __init__(self):
        super().__init__(rate=getattr(settings, 'NOTIFICATION_RATE_LIMIT', '50/hour'))
    
    def get_cache_key(self, request, view) -> str:
        if request.user.is_authenticated:
            return f"notification:user:{request.user.id}"
        return f"notification:ip:{self.get_ident(request)}"


class TelegramWebhookThrottle(RedisThrottle):
    """Rate limiting for Telegram webhook endpoints."""
    
    def __init__(self):
        super().__init__(rate=getattr(settings, 'TELEGRAM_WEBHOOK_RATE_LIMIT', '1000/hour'))
    
    def get_cache_key(self, request, view) -> str:
        # Telegram webhooks should be rate limited by IP
        return f"telegram:webhook:ip:{self.get_ident(request)}"


def get_rate_limit_info(request, throttle_class) -> Dict[str, Any]:
    """
    Get rate limit information for a request.
    
    Args:
        request: Django request object
        throttle_class: Throttle class to check
        
    Returns:
        Dict with rate limit information
    """
    throttle = throttle_class()
    cache_key = throttle.get_cache_key(request, None)
    
    result = throttle.limiter.is_allowed(
        key=cache_key,
        limit=throttle.limit,
        window=throttle.window,
        identifier=getattr(request.user, 'username', 'anonymous')
    )
    
    return result


def clear_rate_limit(key: str) -> bool:
    """
    Clear rate limit for a specific key.
    
    Args:
        key: Rate limit key to clear
        
    Returns:
        True if successful
    """
    try:
        limiter = RedisRateLimiter()
        # Clear all rate limit keys for this identifier
        pattern = f"rate_limit:{key}:*"
        keys = limiter.redis_client.keys(pattern)
        if keys:
            limiter.redis_client.delete(*keys)
        return True
    except Exception:
        return False
