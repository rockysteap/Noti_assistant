# Testing Documentation

This document describes the comprehensive test suite for the notification system.

## Overview

The test suite covers all components of the notification system:
- **Core App**: Models, API endpoints, rate limiting, validation, exception handling
- **Notifications App**: Models, API endpoints, notification workflows
- **Telegram Bot App**: Models, API endpoints, bot functionality, webhooks
- **Integration Tests**: Complete workflows and system integration
- **Performance Tests**: Pagination, search, and ordering performance

## Test Structure

### Test Files

```
apps/
├── core/
│   ├── tests_models.py          # Core model tests
│   ├── tests_api.py             # Core API endpoint tests
│   ├── tests_rate_limiting.py   # Rate limiting tests
│   └── tests_validation.py      # Validation tests
├── notifications/
│   ├── tests_models.py          # Notification model tests
│   └── tests_api.py             # Notification API tests
├── telegram_bot/
│   ├── tests_models.py          # Telegram bot model tests
│   ├── tests_api.py             # Telegram bot API tests
│   └── tests_bot.py             # Bot functionality tests
├── tests_integration.py         # Integration tests
├── tests_config.py              # Test configuration and utilities
└── run_tests.py                 # Test runner script
```

### Test Categories

#### 1. Model Tests (`*_tests_models.py`)
- **Purpose**: Test Django model functionality, relationships, and constraints
- **Coverage**: 
  - Model creation, validation, and constraints
  - Model relationships and foreign keys
  - Model methods and string representations
  - Cascade deletion behavior
  - Default values and field validation

#### 2. API Tests (`*_tests_api.py`)
- **Purpose**: Test REST API endpoints and responses
- **Coverage**:
  - CRUD operations for all models
  - Authentication and authorization
  - Input validation and error handling
  - Pagination, filtering, and search
  - Response format and status codes

#### 3. Feature Tests (`*_tests_*.py`)
- **Purpose**: Test specific features and functionality
- **Coverage**:
  - Rate limiting with Redis
  - Input validation and error handling
  - Telegram bot commands and conversations
  - Webhook processing and security

#### 4. Integration Tests (`tests_integration.py`)
- **Purpose**: Test complete workflows and system integration
- **Coverage**:
  - End-to-end notification workflows
  - Telegram bot integration
  - System-wide integration scenarios
  - Performance and scalability tests

## Running Tests

### Prerequisites

1. **Django Test Settings**: Ensure `noti.settings.test` is properly configured
2. **Test Database**: Tests use a separate test database
3. **Dependencies**: All required packages must be installed

### Running All Tests

```bash
# Using the test runner script
python run_tests.py

# Using Django's test command
python manage.py test

# Using pytest (if installed)
pytest
```

### Running Specific Test Categories

```bash
# Run only model tests
python manage.py test apps.core.tests_models apps.notifications.tests_models apps.telegram_bot.tests_models

# Run only API tests
python manage.py test apps.core.tests_api apps.notifications.tests_api apps.telegram_bot.tests_api

# Run only integration tests
python manage.py test apps.tests_integration

# Run specific app tests
python manage.py test apps.core
python manage.py test apps.notifications
python manage.py test apps.telegram_bot
```

### Running Individual Test Files

```bash
# Run specific test file
python manage.py test apps.core.tests_models

# Run specific test class
python manage.py test apps.core.tests_models.UserProfileModelTestCase

# Run specific test method
python manage.py test apps.core.tests_models.UserProfileModelTestCase.test_user_profile_creation
```

## Test Configuration

### Test Settings

The test configuration is located in `noti.settings.test` and includes:

```python
# Test database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING_CONFIG = None
```

### Test Utilities

The `apps.tests_config.py` file provides:

- **TestDataFactory**: Factory methods for creating test data
- **MockTelegramBot**: Mock Telegram bot for testing
- **TestUtilities**: Utility functions for common test operations
- **TestConstants**: Constants used across tests

## Test Coverage

### Core App Tests

#### Models (`apps.core.tests_models.py`)
- ✅ UserProfile model creation, validation, and relationships
- ✅ SystemSettings model with JSON validation
- ✅ AuditLog model with ordering and relationships
- ✅ Model cascade deletion behavior
- ✅ String representations and default values

#### API Endpoints (`apps.core.tests_api.py`)
- ✅ User CRUD operations
- ✅ UserProfile CRUD operations
- ✅ SystemSettings CRUD operations
- ✅ AuditLog CRUD operations
- ✅ Authentication and authorization
- ✅ Pagination, filtering, and search
- ✅ Error handling and validation

#### Rate Limiting (`apps.core.tests_rate_limiting.py`)
- ✅ Redis-based rate limiting
- ✅ Custom throttle classes
- ✅ Rate limit headers middleware
- ✅ Rate limit exceeded handling
- ✅ Management commands for rate limiting

#### Validation (`apps.core.tests_validation.py`)
- ✅ Custom validators for various data types
- ✅ Enhanced serializers with validation
- ✅ Exception handling and error responses
- ✅ Field-level and object-level validation

### Notifications App Tests

#### Models (`apps.notifications.tests_models.py`)
- ✅ Notification model with scheduling and expiration
- ✅ NotificationTemplate model with template processing
- ✅ NotificationChannel model with configuration
- ✅ NotificationDelivery model with status tracking
- ✅ NotificationSubscription model with user preferences
- ✅ NotificationGroup model with user management
- ✅ NotificationSchedule model with cron expressions

#### API Endpoints (`apps.notifications.tests_api.py`)
- ✅ Notification CRUD operations
- ✅ NotificationTemplate CRUD operations
- ✅ NotificationChannel CRUD operations
- ✅ NotificationDelivery CRUD operations
- ✅ NotificationSubscription CRUD operations
- ✅ NotificationGroup CRUD operations
- ✅ NotificationSchedule CRUD operations
- ✅ Mark as read functionality
- ✅ Unread notifications endpoint

### Telegram Bot App Tests

#### Models (`apps.telegram_bot.tests_models.py`)
- ✅ TelegramUser model with user relationships
- ✅ BotConversation model with state management
- ✅ BotCommand model with command management
- ✅ BotMessage model with message tracking
- ✅ BotWebhook model with webhook configuration
- ✅ BotAnalytics model with analytics data

#### API Endpoints (`apps.telegram_bot.tests_api.py`)
- ✅ TelegramUser CRUD operations
- ✅ BotConversation CRUD operations
- ✅ BotCommand CRUD operations
- ✅ BotMessage CRUD operations
- ✅ BotWebhook CRUD operations
- ✅ BotAnalytics CRUD operations
- ✅ Webhook endpoint testing

#### Bot Functionality (`apps.telegram_bot.tests_bot.py`)
- ✅ Bot command handling
- ✅ Conversation state management
- ✅ Message processing
- ✅ Webhook processing
- ✅ Error handling
- ✅ User management
- ✅ Analytics tracking

### Integration Tests (`apps.tests_integration.py`)

#### Notification Workflows
- ✅ Complete notification creation to delivery workflow
- ✅ Template-based notification creation
- ✅ Subscription management workflow
- ✅ Multi-channel notification delivery

#### Telegram Bot Workflows
- ✅ User registration and profile creation
- ✅ Conversation management
- ✅ Command execution
- ✅ Webhook processing
- ✅ Message handling

#### System Integration
- ✅ System settings management
- ✅ Audit logging
- ✅ User profile management
- ✅ Performance testing

## Test Data Management

### Factory Pattern

The `TestDataFactory` class provides factory methods for creating test data:

```python
# Create a user
user = TestDataFactory.create_user(username='testuser')

# Create a user profile
profile = TestDataFactory.create_user_profile(user, phone_number='+1234567890')

# Create a notification
notification = TestDataFactory.create_notification(user, title='Test')

# Create a Telegram user
telegram_user = TestDataFactory.create_telegram_user(user, telegram_id=123456789)
```

### Mock Objects

The test suite includes mock objects for external services:

```python
# Mock Telegram bot
mock_bot = MockTelegramBot(token='test_token')
mock_bot.send_message(chat_id=123, text='Hello')

# Mock webhook payload
payload = TestUtilities.create_webhook_payload(message_text='Hello bot!')
```

## Performance Testing

### Pagination Tests
- Tests pagination with large datasets
- Verifies page size limits
- Tests navigation between pages

### Search Tests
- Tests search functionality with various queries
- Verifies search performance
- Tests search result accuracy

### Ordering Tests
- Tests ordering by different fields
- Verifies sort order correctness
- Tests performance with large datasets

## Best Practices

### Test Organization
1. **One test class per model/feature**
2. **Descriptive test method names**
3. **Proper setup and teardown**
4. **Independent test methods**
5. **Clear assertions with meaningful messages**

### Test Data
1. **Use factory methods for data creation**
2. **Clean up test data after tests**
3. **Use realistic test data**
4. **Avoid hardcoded values where possible**

### Assertions
1. **Use specific assertions**
2. **Test both positive and negative cases**
3. **Verify side effects**
4. **Check error conditions**

### Mocking
1. **Mock external services**
2. **Mock expensive operations**
3. **Verify mock interactions**
4. **Use realistic mock data**

## Continuous Integration

### GitHub Actions
The test suite can be integrated with GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py
```

### Test Reports
- **Coverage reports**: Generate HTML coverage reports
- **Test results**: Detailed test results with timing
- **Failure analysis**: Clear error messages and stack traces

## Troubleshooting

### Common Issues

1. **Database errors**: Ensure test database is properly configured
2. **Import errors**: Check that all dependencies are installed
3. **Permission errors**: Verify file permissions for test files
4. **Timeout errors**: Increase timeout values for slow tests

### Debug Mode

Run tests in debug mode for detailed output:

```bash
python manage.py test --verbosity=2 --debug-mode
```

### Test Isolation

Ensure tests are isolated and don't affect each other:

```python
def setUp(self):
    """Set up test data for each test method."""
    self.user = TestDataFactory.create_user()
    self.client = TestUtilities.create_authenticated_client(self.user)
```

## Conclusion

The comprehensive test suite ensures the notification system is robust, reliable, and maintainable. All components are thoroughly tested with both unit tests and integration tests, providing confidence in the system's functionality and performance.
