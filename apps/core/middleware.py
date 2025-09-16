"""
Custom middleware for the Noti project.
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from apps.core.rate_limiting import get_rate_limit_info, AnonRateThrottle, UserRateThrottle


class RateLimitHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add rate limit headers to responses.
    """
    
    def process_response(self, request, response):
        """Add rate limit headers to response."""
        try:
            # Get rate limit info for the request
            if request.user.is_authenticated:
                rate_info = get_rate_limit_info(request, UserRateThrottle)
            else:
                rate_info = get_rate_limit_info(request, AnonRateThrottle)
            
            # Add rate limit headers
            response['X-RateLimit-Limit'] = rate_info['limit']
            response['X-RateLimit-Remaining'] = rate_info['remaining']
            response['X-RateLimit-Reset'] = rate_info['reset_time']
            
            if rate_info['retry_after'] > 0:
                response['Retry-After'] = rate_info['retry_after']
                
        except Exception:
            # If rate limiting fails, don't break the response
            pass
            
        return response


class RateLimitExceededMiddleware(MiddlewareMixin):
    """
    Middleware to handle rate limit exceeded responses.
    """
    
    def process_response(self, request, response):
        """Handle rate limit exceeded responses."""
        if response.status_code == 429:  # Too Many Requests
            try:
                if request.user.is_authenticated:
                    rate_info = get_rate_limit_info(request, UserRateThrottle)
                else:
                    rate_info = get_rate_limit_info(request, AnonRateThrottle)
                
                # Return JSON response for API requests
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': f'You have exceeded the rate limit of {rate_info["limit"]} requests per {rate_info["window"]} seconds',
                        'retry_after': rate_info['retry_after'],
                        'limit': rate_info['limit'],
                        'remaining': rate_info['remaining'],
                        'reset_time': rate_info['reset_time']
                    }, status=429)
                    
            except Exception:
                pass
                
        return response
