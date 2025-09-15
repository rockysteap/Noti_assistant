# Noti API Documentation

This document provides comprehensive documentation for the Noti notification system API.

## Base URL
```
http://localhost:8000/api/
```

## Authentication
The API uses Django REST Framework's built-in authentication. All endpoints require authentication unless specified otherwise.

### Authentication Methods
- **Session Authentication**: For web browser access
- **Token Authentication**: For API clients
- **Admin Access**: Required for system management endpoints

## API Endpoints

### Core App (`/api/`)

#### Users
- `GET /api/users/` - List all users (Admin only)
- `GET /api/users/{id}/` - Get user details
- `GET /api/users/me/` - Get current user information
- `POST /api/users/` - Create user (Admin only)
- `PUT /api/users/{id}/` - Update user (Admin only)
- `DELETE /api/users/{id}/` - Delete user (Admin only)

#### User Profiles
- `GET /api/profiles/` - List all profiles
- `GET /api/profiles/{id}/` - Get profile details
- `GET /api/profiles/me/` - Get/Update current user's profile
- `PATCH /api/profiles/me/` - Update current user's profile
- `POST /api/profiles/` - Create profile
- `PUT /api/profiles/{id}/` - Update profile
- `DELETE /api/profiles/{id}/` - Delete profile

#### System Settings
- `GET /api/settings/` - List all settings (Admin only)
- `GET /api/settings/{id}/` - Get setting details (Admin only)
- `GET /api/settings/active/` - Get active settings
- `POST /api/settings/` - Create setting (Admin only)
- `PUT /api/settings/{id}/` - Update setting (Admin only)
- `DELETE /api/settings/{id}/` - Delete setting (Admin only)

#### Audit Logs
- `GET /api/audit-logs/` - List audit logs (Admin only)
- `GET /api/audit-logs/{id}/` - Get audit log details (Admin only)

### Telegram Bot App (`/api/telegram/`)

#### Telegram Users
- `GET /api/telegram/users/` - List all Telegram users
- `GET /api/telegram/users/{id}/` - Get Telegram user details
- `POST /api/telegram/users/` - Create Telegram user
- `PUT /api/telegram/users/{id}/` - Update Telegram user
- `DELETE /api/telegram/users/{id}/` - Delete Telegram user

#### Bot Conversations
- `GET /api/telegram/conversations/` - List all conversations
- `GET /api/telegram/conversations/{id}/` - Get conversation details
- `POST /api/telegram/conversations/` - Create conversation
- `PUT /api/telegram/conversations/{id}/` - Update conversation
- `DELETE /api/telegram/conversations/{id}/` - Delete conversation

#### Bot Commands
- `GET /api/telegram/commands/` - List all commands
- `GET /api/telegram/commands/{id}/` - Get command details
- `GET /api/telegram/commands/active/` - Get active commands
- `POST /api/telegram/commands/` - Create command
- `PUT /api/telegram/commands/{id}/` - Update command
- `DELETE /api/telegram/commands/{id}/` - Delete command

#### Bot Messages
- `GET /api/telegram/messages/` - List all messages (Read-only)
- `GET /api/telegram/messages/{id}/` - Get message details (Read-only)

#### Bot Webhooks
- `GET /api/telegram/webhooks/` - List all webhooks (Admin only)
- `GET /api/telegram/webhooks/{id}/` - Get webhook details (Admin only)
- `POST /api/telegram/webhooks/` - Create webhook (Admin only)
- `PUT /api/telegram/webhooks/{id}/` - Update webhook (Admin only)
- `DELETE /api/telegram/webhooks/{id}/` - Delete webhook (Admin only)

#### Bot Analytics
- `GET /api/telegram/analytics/` - List analytics (Read-only)
- `GET /api/telegram/analytics/{id}/` - Get analytics details (Read-only)

### Notifications App (`/api/notifications/`)

#### Notifications
- `GET /api/notifications/` - List user's notifications
- `GET /api/notifications/{id}/` - Get notification details
- `GET /api/notifications/unread/` - Get unread notifications
- `POST /api/notifications/{id}/mark_read/` - Mark notification as read
- `POST /api/notifications/mark_all_read/` - Mark all notifications as read
- `POST /api/notifications/` - Create notification
- `PUT /api/notifications/{id}/` - Update notification
- `DELETE /api/notifications/{id}/` - Delete notification

#### Notification Templates
- `GET /api/notifications/templates/` - List all templates
- `GET /api/notifications/templates/{id}/` - Get template details
- `GET /api/notifications/templates/active/` - Get active templates
- `POST /api/notifications/templates/` - Create template
- `PUT /api/notifications/templates/{id}/` - Update template
- `DELETE /api/notifications/templates/{id}/` - Delete template

#### Notification Channels
- `GET /api/notifications/channels/` - List all channels
- `GET /api/notifications/channels/{id}/` - Get channel details
- `GET /api/notifications/channels/active/` - Get active channels
- `POST /api/notifications/channels/` - Create channel
- `PUT /api/notifications/channels/{id}/` - Update channel
- `DELETE /api/notifications/channels/{id}/` - Delete channel

#### Notification Deliveries
- `GET /api/notifications/deliveries/` - List all deliveries (Read-only)
- `GET /api/notifications/deliveries/{id}/` - Get delivery details (Read-only)

#### Notification Subscriptions
- `GET /api/notifications/subscriptions/` - List user's subscriptions
- `GET /api/notifications/subscriptions/{id}/` - Get subscription details
- `GET /api/notifications/subscriptions/me/` - Get current user's subscriptions
- `POST /api/notifications/subscriptions/` - Create subscription
- `PUT /api/notifications/subscriptions/{id}/` - Update subscription
- `DELETE /api/notifications/subscriptions/{id}/` - Delete subscription

#### Notification Groups
- `GET /api/notifications/groups/` - List all groups
- `GET /api/notifications/groups/{id}/` - Get group details
- `POST /api/notifications/groups/` - Create group
- `PUT /api/notifications/groups/{id}/` - Update group
- `DELETE /api/notifications/groups/{id}/` - Delete group

#### Notification Schedules
- `GET /api/notifications/schedules/` - List all schedules
- `GET /api/notifications/schedules/{id}/` - Get schedule details
- `GET /api/notifications/schedules/active/` - Get active schedules
- `POST /api/notifications/schedules/` - Create schedule
- `PUT /api/notifications/schedules/{id}/` - Update schedule
- `DELETE /api/notifications/schedules/{id}/` - Delete schedule

## Query Parameters

### Filtering
Most list endpoints support filtering using query parameters:
- `?field=value` - Filter by exact match
- `?field__in=value1,value2` - Filter by multiple values
- `?field__contains=value` - Filter by partial match
- `?field__gte=value` - Filter by greater than or equal
- `?field__lte=value` - Filter by less than or equal

### Searching
Endpoints with search support use the `search` parameter:
- `?search=query` - Search across multiple fields

### Ordering
Most endpoints support ordering using the `ordering` parameter:
- `?ordering=field` - Order by field ascending
- `?ordering=-field` - Order by field descending
- `?ordering=field1,-field2` - Order by multiple fields

### Pagination
All list endpoints support pagination:
- `?page=1` - Get specific page
- `?page_size=20` - Set page size (default: 20)

## Response Format

### Success Response
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/endpoint/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "field1": "value1",
            "field2": "value2",
            "created_at": "2025-01-15T10:30:00Z"
        }
    ]
}
```

### Error Response
```json
{
    "field_name": [
        "This field is required."
    ],
    "non_field_errors": [
        "General error message."
    ]
}
```

## Authentication Examples

### Using Token Authentication
```bash
curl -H "Authorization: Token your-token-here" \
     -H "Accept: application/json" \
     http://localhost:8000/api/notifications/
```

### Using Session Authentication
```bash
curl -H "Accept: application/json" \
     -c cookies.txt \
     -b cookies.txt \
     http://localhost:8000/api/notifications/
```

## Webhook Endpoints

### Telegram Webhook
- `POST /webhook/telegram/` - Telegram bot webhook (No authentication required)

## Health Check Endpoints

- `GET /health/` - Basic health check
- `GET /health/database/` - Database health check
- `GET /health/redis/` - Redis health check

## Rate Limiting

The API implements rate limiting:
- Anonymous users: 100 requests per hour
- Authenticated users: 1000 requests per hour

## Error Codes

- `200` - OK
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error
