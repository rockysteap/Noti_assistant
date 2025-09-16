#!/usr/bin/env python
"""
Test runner script for the notification system.
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Setup Django for testing."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'noti.settings.test')
    django.setup()

def run_tests():
    """Run all tests."""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Test patterns to run
    test_patterns = [
        'apps.core.tests_models',
        'apps.core.tests_api',
        'apps.core.tests_rate_limiting',
        'apps.core.tests_validation',
        'apps.notifications.tests_models',
        'apps.notifications.tests_api',
        'apps.telegram_bot.tests_models',
        'apps.telegram_bot.tests_api',
        'apps.telegram_bot.tests_bot',
        'apps.tests_integration',
    ]
    
    print("Running notification system tests...")
    print("=" * 50)
    
    failures = test_runner.run_tests(test_patterns)
    
    if failures:
        print(f"\n❌ {failures} test(s) failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == '__main__':
    run_tests()
