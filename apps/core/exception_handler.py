"""
Custom exception handler for the Noti project.
"""

import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from apps.core.exceptions import (
    NotiAPIException, ValidationError, AuthenticationError, PermissionError,
    NotFoundError, ConflictError, RateLimitError, ServiceUnavailableError,
    NotificationError, TelegramBotError, DatabaseError, ExternalServiceError,
    handle_validation_error, handle_permission_denied, create_error_response
)

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for the Noti API.
    
    Args:
        exc: The exception that was raised
        context: Dictionary containing any additional context
        
    Returns:
        Response object with standardized error format
    """
    # Get the request from context
    request = context.get('request')
    
    # Log the exception
    logger.error(f"Exception occurred: {exc}", exc_info=True, extra={
        'request': request,
        'view': context.get('view'),
        'exception_type': type(exc).__name__
    })
    
    # Handle Django ValidationError
    if isinstance(exc, DjangoValidationError):
        return handle_validation_error(exc, context)
    
    # Handle Django PermissionDenied
    if isinstance(exc, PermissionDenied):
        return handle_permission_denied(exc, context)
    
    # Handle custom NotiAPIException
    if isinstance(exc, NotiAPIException):
        return create_error_response(exc, request)
    
    # Handle DRF APIException
    if isinstance(exc, APIException):
        return handle_drf_exception(exc, request)
    
    # Handle other exceptions
    return handle_generic_exception(exc, request)


def handle_drf_exception(exc, request):
    """
    Handle DRF APIException.
    """
    response_data = {
        'error': {
            'code': getattr(exc, 'default_code', 'api_error'),
            'message': str(exc.detail),
            'type': exc.__class__.__name__
        }
    }
    
    # Add field errors for validation errors
    if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
        field_errors = {}
        for field, errors in exc.detail.items():
            if isinstance(errors, list):
                field_errors[field] = [str(error) for error in errors]
            else:
                field_errors[field] = [str(errors)]
        
        if field_errors:
            response_data['error']['fields'] = field_errors
    
    # Add retry_after for rate limit errors
    if hasattr(exc, 'wait') and exc.wait:
        response_data['error']['retry_after'] = exc.wait
    
    return JsonResponse(
        response_data,
        status=exc.status_code
    )


def handle_generic_exception(exc, request):
    """
    Handle generic exceptions.
    """
    # Log the exception
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={
        'request': request,
        'exception_type': type(exc).__name__
    })
    
    response_data = {
        'error': {
            'code': 'internal_server_error',
            'message': 'An unexpected error occurred. Please try again later.',
            'type': 'InternalServerError'
        }
    }
    
    # In development, include more details
    from django.conf import settings
    if settings.DEBUG:
        response_data['error']['details'] = str(exc)
        response_data['error']['type'] = type(exc).__name__
    
    return JsonResponse(
        response_data,
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def handle_validation_error_response(serializer_errors):
    """
    Handle serializer validation errors and return standardized response.
    
    Args:
        serializer_errors: Dictionary of field errors from serializer
        
    Returns:
        JsonResponse with standardized error format
    """
    field_errors = {}
    
    for field, errors in serializer_errors.items():
        if isinstance(errors, list):
            field_errors[field] = [str(error) for error in errors]
        else:
            field_errors[field] = [str(errors)]
    
    response_data = {
        'error': {
            'code': 'validation_error',
            'message': 'Validation failed',
            'type': 'ValidationError',
            'fields': field_errors
        }
    }
    
    return JsonResponse(
        response_data,
        status=status.HTTP_400_BAD_REQUEST
    )


def handle_permission_error_response(message="Permission denied"):
    """
    Handle permission errors and return standardized response.
    
    Args:
        message: Error message
        
    Returns:
        JsonResponse with standardized error format
    """
    response_data = {
        'error': {
            'code': 'permission_denied',
            'message': message,
            'type': 'PermissionError'
        }
    }
    
    return JsonResponse(
        response_data,
        status=status.HTTP_403_FORBIDDEN
    )


def handle_not_found_error_response(resource="Resource"):
    """
    Handle not found errors and return standardized response.
    
    Args:
        resource: Name of the resource that was not found
        
    Returns:
        JsonResponse with standardized error format
    """
    response_data = {
        'error': {
            'code': 'not_found',
            'message': f"{resource} not found",
            'type': 'NotFoundError'
        }
    }
    
    return JsonResponse(
        response_data,
        status=status.HTTP_404_NOT_FOUND
    )


def handle_rate_limit_error_response(retry_after=None):
    """
    Handle rate limit errors and return standardized response.
    
    Args:
        retry_after: Seconds to wait before retrying
        
    Returns:
        JsonResponse with standardized error format
    """
    response_data = {
        'error': {
            'code': 'rate_limit_exceeded',
            'message': 'Rate limit exceeded. Please try again later.',
            'type': 'RateLimitError'
        }
    }
    
    if retry_after:
        response_data['error']['retry_after'] = retry_after
    
    return JsonResponse(
        response_data,
        status=status.HTTP_429_TOO_MANY_REQUESTS
    )


class ErrorResponseMixin:
    """
    Mixin for views to provide standardized error responses.
    """
    
    def validation_error_response(self, serializer_errors):
        """Return validation error response."""
        return handle_validation_error_response(serializer_errors)
    
    def permission_error_response(self, message="Permission denied"):
        """Return permission error response."""
        return handle_permission_error_response(message)
    
    def not_found_error_response(self, resource="Resource"):
        """Return not found error response."""
        return handle_not_found_error_response(resource)
    
    def rate_limit_error_response(self, retry_after=None):
        """Return rate limit error response."""
        return handle_rate_limit_error_response(retry_after)
