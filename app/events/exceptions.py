"""
Event-specific exceptions for the event-driven architecture.

This module contains exception classes specific to event processing,
handling, and dispatching.
"""

from app.core.exceptions import AppException
from fastapi import status

class EventException(AppException):
    """Base exception for all event-related errors."""
    def __init__(
        self, 
        message: str, 
        error_code: str = "EVENT_ERROR",
        details: str = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details
        )

class EventDispatchError(EventException):
    """Raised when an event fails to be dispatched."""
    def __init__(self, event_type: str, message: str = None, details: str = None):
        error_message = message or f"Failed to dispatch event of type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_DISPATCH_ERROR",
            details=details
        )

class EventHandlerError(EventException):
    """Raised when an event handler fails to process an event."""
    def __init__(self, event_type: str, handler_name: str, message: str = None, details: str = None):
        error_message = message or f"Error in handler '{handler_name}' for event type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_HANDLER_ERROR",
            details=details
        )

class EventRetryError(EventException):
    """Raised when an event handler retry fails."""
    def __init__(
        self, 
        event_type: str, 
        handler_name: str, 
        retry_count: int, 
        max_retries: int, 
        message: str = None, 
        details: str = None
    ):
        error_message = message or f"Failed to process event type '{event_type}' in handler '{handler_name}' after {retry_count} retries"
        super().__init__(
            message=error_message,
            error_code="EVENT_RETRY_ERROR",
            details=details
        )
        self.retry_count = retry_count
        self.max_retries = max_retries

class EventValidationError(EventException):
    """Raised when an event fails validation."""
    def __init__(self, event_type: str, message: str = None, details: str = None):
        error_message = message or f"Event validation failed for event type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_VALIDATION_ERROR",
            details=details
        )

class EventSerializationError(EventException):
    """Raised when event serialization fails."""
    def __init__(self, event_type: str, message: str = None, details: str = None):
        error_message = message or f"Failed to serialize event of type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_SERIALIZATION_ERROR",
            details=details
        )

class EventDeserializationError(EventException):
    """Raised when event deserialization fails."""
    def __init__(self, event_type: str, message: str = None, details: str = None):
        error_message = message or f"Failed to deserialize event of type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_DESERIALIZATION_ERROR",
            details=details
        )

class EventSubscriptionError(EventException):
    """Raised when there is an error in event subscription."""
    def __init__(self, event_type: str, message: str = None, details: str = None):
        error_message = message or f"Error in subscription for event type: {event_type}"
        super().__init__(
            message=error_message,
            error_code="EVENT_SUBSCRIPTION_ERROR",
            details=details
        ) 