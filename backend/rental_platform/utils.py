from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging
import traceback
import sys

logger = logging.getLogger('django')

def custom_exception_handler(exc, context):
    """
    Custom exception handler that improves error reporting, especially for 500 errors.
    """
    # First, get the standard DRF exception response
    response = exception_handler(exc, context)
    
    # Log the exception regardless of whether it's handled or not
    request = context.get('request')
    view = context.get('view')
    view_name = view.__class__.__name__ if hasattr(view, '__class__') else 'Unknown View'
    
    # Get the URL path for better error context
    path = request.path if hasattr(request, 'path') else 'unknown path'
    
    # Extra logging for booking-related views to help diagnose issues
    is_booking_view = 'booking' in view_name.lower() if view_name else False
    
    # If this is a listing endpoint (GET request), we should never return a 500 error
    is_listing_request = request.method == 'GET' and path.endswith('/')
    
    # If no response is returned by DRF, it means we have an unhandled exception
    if response is None:
        # Log the full exception traceback for debugging
        exc_info = sys.exc_info()
        stack_trace = ''.join(traceback.format_exception(*exc_info))
        
        # Log with detailed information about the request and error
        log_prefix = '[BOOKING ERROR] ' if is_booking_view else '[ERROR] '
        
        logger.error(
            f"{log_prefix}Unhandled exception in {view_name} handling {request.method} to {path}\n"
            f"User: {request.user}\n"
            f"Data: {request.data if hasattr(request, 'data') else 'No data'}\n"
            f"Error: {exc.__class__.__name__}: {str(exc)}\n"
            f"Traceback:\n{stack_trace}"
        )
        
        # For listing requests, return an empty list instead of an error
        if is_listing_request and is_booking_view:
            logger.warning(f"Returning empty list for failed booking listing request to {path}")
            
            # For GET requests to collection endpoints, return an empty paginated response instead of 500
            if path.endswith('/bookings/') or '/bookings' in path:
                return Response({
                    'count': 0,
                    'next': None,
                    'previous': None,
                    'results': []
                })
            return Response([])  # Empty list for non-paginated endpoints
        
        # Customize the error message without exposing sensitive information
        error_message = f"A server error occurred. Please contact support with reference: {view_name}-{exc.__class__.__name__}"
        
        # For booking errors, provide more context if possible
        if is_booking_view:
            try:
                booking_data = request.data if hasattr(request, 'data') else {}
                property_id = booking_data.get('property', 'unknown')
                error_message = f"Error with booking operation. Please try again or contact support."
            except Exception as context_error:
                logger.warning(f"Failed to provide better context for booking error: {context_error}")
        
        # Return a proper 500 response
        return Response(
            {'detail': error_message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    else:
        # For handled exceptions, add more logging for booking views
        if is_booking_view:
            logger.info(
                f"[BOOKING] Handled exception in {view_name}: "
                f"{exc.__class__.__name__}: {str(exc)}\n"
                f"Response status: {response.status_code}\n"
                f"Response data: {response.data}"
            )
    
    # For handled exceptions, just return the standard response
    return response

def custom_exception_handler_old(exc, context):
    """
    Custom exception handler for REST framework that formats errors consistently.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If there's an unhandled exception, return a custom response
    if response is None:
        if isinstance(exc, DjangoValidationError):
            # Handle Django validation errors
            errors = {}
            if hasattr(exc, 'error_dict'):
                for field, field_errors in exc.error_dict.items():
                    errors[field] = [str(e) for e in field_errors]
            else:
                errors['detail'] = [str(e) for e in exc.error_list]
            
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        
        elif isinstance(exc, Http404):
            # Handle 404 errors
            return Response(
                {'detail': 'Not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Handle other unhandled exceptions
        return Response(
            {'detail': 'A server error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Reformat DRF validation errors
    if isinstance(exc, DRFValidationError) and isinstance(response.data, dict):
        errors = {}
        for key, value in response.data.items():
            if isinstance(value, list):
                errors[key] = value
            else:
                errors[key] = [str(value)]
        
        response.data = {'errors': errors}
    
    return response 