"""
Management command for rate limiting operations.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.core.rate_limiting import clear_rate_limit, RedisRateLimiter
from django.conf import settings


class Command(BaseCommand):
    help = 'Manage rate limiting for users and IPs'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['clear', 'status', 'test'],
            help='Action to perform: clear, status, or test'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username or user ID to clear rate limit for'
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='IP address to clear rate limit for'
        )
        parser.add_argument(
            '--key',
            type=str,
            help='Specific rate limit key to clear'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Rate limit for testing (default: 10)'
        )
        parser.add_argument(
            '--window',
            type=int,
            default=60,
            help='Time window in seconds for testing (default: 60)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'clear':
            self.clear_rate_limits(options)
        elif action == 'status':
            self.show_status(options)
        elif action == 'test':
            self.test_rate_limiting(options)

    def clear_rate_limits(self, options):
        """Clear rate limits for specified user, IP, or key."""
        cleared = []
        
        if options['user']:
            try:
                if options['user'].isdigit():
                    user = User.objects.get(id=int(options['user']))
                else:
                    user = User.objects.get(username=options['user'])
                
                key = f"user:{user.id}"
                if clear_rate_limit(key):
                    cleared.append(f"User {user.username} (ID: {user.id})")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to clear rate limit for user {user.username}")
                    )
            except User.DoesNotExist:
                raise CommandError(f"User '{options['user']}' not found")
        
        if options['ip']:
            key = f"ip:{options['ip']}"
            if clear_rate_limit(key):
                cleared.append(f"IP {options['ip']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"Failed to clear rate limit for IP {options['ip']}")
                )
        
        if options['key']:
            if clear_rate_limit(options['key']):
                cleared.append(f"Key {options['key']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"Failed to clear rate limit for key {options['key']}")
                )
        
        if not options['user'] and not options['ip'] and not options['key']:
            # Clear all rate limits
            limiter = RedisRateLimiter()
            try:
                keys = limiter.redis_client.keys("rate_limit:*")
                if keys:
                    limiter.redis_client.delete(*keys)
                    cleared.append(f"All rate limits ({len(keys)} keys)")
                else:
                    self.stdout.write(self.style.WARNING("No rate limit keys found"))
            except Exception as e:
                raise CommandError(f"Failed to clear all rate limits: {e}")
        
        if cleared:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully cleared rate limits for: {', '.join(cleared)}")
            )
        else:
            self.stdout.write(self.style.WARNING("No rate limits were cleared"))

    def show_status(self, options):
        """Show current rate limiting status."""
        limiter = RedisRateLimiter()
        
        try:
            # Get all rate limit keys
            keys = limiter.redis_client.keys("rate_limit:*")
            
            if not keys:
                self.stdout.write("No active rate limits found")
                return
            
            self.stdout.write(f"Found {len(keys)} active rate limit keys:")
            self.stdout.write("-" * 50)
            
            for key in sorted(keys):
                # Decode key if it's bytes
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # Get key info
                ttl = limiter.redis_client.ttl(key)
                count = limiter.redis_client.zcard(key)
                
                self.stdout.write(f"Key: {key}")
                self.stdout.write(f"  Count: {count}")
                self.stdout.write(f"  TTL: {ttl} seconds")
                self.stdout.write("")
                
        except Exception as e:
            raise CommandError(f"Failed to get rate limit status: {e}")

    def test_rate_limiting(self, options):
        """Test rate limiting functionality."""
        limit = options['limit']
        window = options['window']
        
        self.stdout.write(f"Testing rate limiting: {limit} requests per {window} seconds")
        self.stdout.write("-" * 50)
        
        limiter = RedisRateLimiter()
        test_key = "test:rate_limit"
        
        # Clear any existing test data
        clear_rate_limit(test_key)
        
        # Test rate limiting
        for i in range(limit + 5):  # Try to exceed the limit
            result = limiter.is_allowed(
                key=test_key,
                limit=limit,
                window=window,
                identifier=f"test_user_{i}"
            )
            
            status = "ALLOWED" if result['allowed'] else "BLOCKED"
            self.stdout.write(
                f"Request {i+1:2d}: {status:7s} | "
                f"Remaining: {result['remaining']:2d} | "
                f"Retry after: {result['retry_after']:2d}s"
            )
            
            if not result['allowed']:
                self.stdout.write(
                    self.style.WARNING(f"Rate limit exceeded at request {i+1}")
                )
                break
        
        # Clean up test data
        clear_rate_limit(test_key)
        self.stdout.write(self.style.SUCCESS("Rate limiting test completed"))
