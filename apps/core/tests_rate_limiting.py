"""
Tests for rate limiting functionality.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from apps.core.rate_limiting import RedisRateLimiter, UserRateThrottle, AnonRateThrottle
from unittest.mock import patch


class RateLimitingTestCase(TestCase):
    """Test cases for rate limiting functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.limiter = RedisRateLimiter()
    
    def test_redis_rate_limiter_basic(self):
        """Test basic rate limiting functionality."""
        key = "test:rate_limit"
        limit = 5
        window = 60
        
        # Clear any existing data
        self.limiter.redis_client.delete(f"rate_limit:{key}:0")
        
        # Test within limit
        for i in range(limit):
            result = self.limiter.is_allowed(key, limit, window, f"test_{i}")
            self.assertTrue(result['allowed'])
            self.assertEqual(result['remaining'], limit - i - 1)
        
        # Test exceeding limit
        result = self.limiter.is_allowed(key, limit, window, "test_exceed")
        self.assertFalse(result['allowed'])
        self.assertEqual(result['remaining'], 0)
        self.assertGreater(result['retry_after'], 0)
    
    def test_user_rate_throttle(self):
        """Test user rate throttling."""
        request = self.factory.get('/api/test/')
        request.user = self.user
        
        throttle = UserRateThrottle()
        
        # Test multiple requests
        for i in range(5):  # Should be within limit
            allowed = throttle.allow_request(request, None)
            self.assertTrue(allowed)
    
    def test_anon_rate_throttle(self):
        """Test anonymous rate throttling."""
        request = self.factory.get('/api/test/')
        request.user = None
        
        throttle = AnonRateThrottle()
        
        # Test multiple requests
        for i in range(5):  # Should be within limit
            allowed = throttle.allow_request(request, None)
            self.assertTrue(allowed)
    
    @patch('apps.core.rate_limiting.cache.client.get_client')
    def test_rate_limiter_with_mock_redis(self, mock_get_client):
        """Test rate limiter with mocked Redis client."""
        # Mock Redis client
        mock_redis = mock_get_client.return_value
        mock_redis.pipeline.return_value.execute.return_value = [0, 5, 0, True]  # Mock pipeline results
        
        limiter = RedisRateLimiter()
        result = limiter.is_allowed("test_key", 10, 60, "test_user")
        
        self.assertTrue(result['allowed'])
        self.assertEqual(result['remaining'], 4)  # 10 - 5 - 1
    
    def tearDown(self):
        """Clean up test data."""
        # Clear any test rate limit keys
        pattern = "rate_limit:test:*"
        keys = self.limiter.redis_client.keys(pattern)
        if keys:
            self.limiter.redis_client.delete(*keys)
