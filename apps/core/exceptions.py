"""
Custom exceptions for the Noti project.
"""

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _


class NotiAPIException(APIException):
    """
    Base exception for Noti API.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('A server error occurred.')
    default_code = 'error'
    
    def __init__(self, detail=None, code=None, status_code=None):
        if status_code:
            self.status_code = status_code
        super().__init__(detail, code)


class ValidationError(NotiAPIException):
    """
    Custom validation error with detailed field information.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Invalid input.')
    default_code = 'validation_error'
    
    def __init__(self, detail=None, field_errors=None):
        self.field_errors = field_errors or {}
        super().__init__(detail)


class AuthenticationError(NotiAPIException):
    """
    Authentication error.
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _('Authentication credentials were not provided.')
    default_code = 'authentication_failed'


class PermissionError(NotiAPIException):
    """
    Permission denied error.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _('You do not have permission to perform this action.')
    default_code = 'permission_denied'


class NotFoundError(NotiAPIException):
    """
    Resource not found error.
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('The requested resource was not found.')
    default_code = 'not_found'


class ConflictError(NotiAPIException):
    """
    Resource conflict error.
    """
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('The request conflicts with the current state of the resource.')
    default_code = 'conflict'


class RateLimitError(NotiAPIException):
    """
    Rate limit exceeded error.
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _('Rate limit exceeded. Please try again later.')
    default_code = 'rate_limit_exceeded'
    
    def __init__(self, detail=None, retry_after=None):
        self.retry_after = retry_after
        super().__init__(detail)


class ServiceUnavailableError(NotiAPIException):
    """
    Service unavailable error.
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = _('Service temporarily unavailable. Please try again later.')
    default_code = 'service_unavailable'


class NotificationError(NotiAPIException):
    """
    Notification-specific error.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Notification error occurred.')
    default_code = 'notification_error'


class TelegramBotError(NotiAPIException):
    """
    Telegram bot-specific error.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Telegram bot error occurred.')
    default_code = 'telegram_bot_error'


class DatabaseError(NotiAPIException):
    """
    Database operation error.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _('Database error occurred.')
    default_code = 'database_error'


class ExternalServiceError(NotiAPIException):
    """
    External service error.
    """
    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = _('External service error occurred.')
    default_code = 'external_service_error'


def handle_validation_error(exc, context=None):
    """
    Handle Django ValidationError and convert to DRF format.
    """
    if hasattr(exc, 'message_dict'):
        # Field-specific errors
        field_errors = {}
        for field, messages in exc.message_dict.items():
            if isinstance(messages, list):
                field_errors[field] = [str(msg) for msg in messages]
            else:
                field_errors[field] = [str(messages)]
        
        return ValidationError(
            detail="Validation failed",
            field_errors=field_errors
        )
    else:
        # General validation error
        return ValidationError(detail=str(exc))


def handle_permission_denied(exc, context=None):
    """
    Handle Django PermissionDenied and convert to DRF format.
    """
    return PermissionError(detail=str(exc) or "Permission denied")


def create_error_response(error, request=None):
    """
    Create a standardized error response.
    """
    response_data = {
        'error': {
            'code': getattr(error, 'default_code', 'error'),
            'message': str(error.detail) if hasattr(error, 'detail') else str(error),
            'type': error.__class__.__name__
        }
    }
    
    # Add field errors if available
    if hasattr(error, 'field_errors') and error.field_errors:
        response_data['error']['fields'] = error.field_errors
    
    # Add retry_after for rate limit errors
    if hasattr(error, 'retry_after') and error.retry_after:
        response_data['error']['retry_after'] = error.retry_after
    
    # Add request ID for tracking
    if request and hasattr(request, 'id'):
        response_data['error']['request_id'] = request.id
    
    return JsonResponse(
        response_data,
        status=getattr(error, 'status_code', status.HTTP_400_BAD_REQUEST)
    )


class ErrorCodes:
    """
    Centralized error codes for the application.
    """
    # General errors
    VALIDATION_ERROR = 'validation_error'
    AUTHENTICATION_FAILED = 'authentication_failed'
    PERMISSION_DENIED = 'permission_denied'
    NOT_FOUND = 'not_found'
    CONFLICT = 'conflict'
    RATE_LIMIT_EXCEEDED = 'rate_limit_exceeded'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    
    # Notification errors
    NOTIFICATION_SEND_FAILED = 'notification_send_failed'
    NOTIFICATION_TEMPLATE_INVALID = 'notification_template_invalid'
    NOTIFICATION_CHANNEL_UNAVAILABLE = 'notification_channel_unavailable'
    NOTIFICATION_USER_NOT_SUBSCRIBED = 'notification_user_not_subscribed'
    
    # Telegram bot errors
    TELEGRAM_API_ERROR = 'telegram_api_error'
    TELEGRAM_WEBHOOK_INVALID = 'telegram_webhook_invalid'
    TELEGRAM_USER_NOT_FOUND = 'telegram_user_not_found'
    TELEGRAM_COMMAND_NOT_FOUND = 'telegram_command_not_found'
    
    # Database errors
    DATABASE_CONNECTION_ERROR = 'database_connection_error'
    DATABASE_QUERY_ERROR = 'database_query_error'
    DATABASE_CONSTRAINT_ERROR = 'database_constraint_error'
    
    # External service errors
    EMAIL_SERVICE_ERROR = 'email_service_error'
    SMS_SERVICE_ERROR = 'sms_service_error'
    PUSH_SERVICE_ERROR = 'push_service_error'
    WEBHOOK_SERVICE_ERROR = 'webhook_service_error'
