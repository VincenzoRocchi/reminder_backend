"""
Utility functions for working with events.

This module provides helper functions for event-related operations,
including safe event emission and background processing.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, TypeVar

from app.events.base import Event
from app.events.dispatcher import event_dispatcher
from app.events.exceptions import EventDispatchError

logger = logging.getLogger(__name__)

T = TypeVar('T')

def emit_event_safely(event: Event) -> None:
    """
    Emit an event with additional error handling to ensure service operations
    are not disrupted if event emission fails.
    
    Args:
        event: The event to emit
    """
    try:
        event_dispatcher.emit(event)
    except Exception as e:
        logger.error(
            f"Failed to emit event of type {event.event_type}: {str(e)}",
            exc_info=True
        )

async def emit_event_async_safely(event: Event) -> None:
    """
    Emit an event asynchronously with additional error handling.
    
    Args:
        event: The event to emit
    """
    try:
        await event_dispatcher.emit_async(event)
    except Exception as e:
        logger.error(
            f"Failed to emit async event of type {event.event_type}: {str(e)}",
            exc_info=True
        )

def background_event_emission(func: Callable) -> Callable:
    """
    Decorator for emitting events in the background without waiting.
    
    This decorator is useful for service methods that emit events but don't
    need to wait for the event processing to complete.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # The last argument is expected to be the event
        if args and isinstance(args[-1], Event):
            event = args[-1]
            try:
                asyncio.create_task(emit_event_async_safely(event))
            except Exception as e:
                logger.error(
                    f"Failed to schedule background event emission for {event.event_type}: {str(e)}",
                    exc_info=True
                )
        return result
    return wrapper

def with_event_emission(event_factory: Callable[..., Event]) -> Callable:
    """
    Decorator that emits an event after a function completes successfully.
    
    This decorator is useful for automatically emitting events after
    service methods complete. The event_factory function should take the same
    arguments as the decorated function plus the function's result.
    
    Args:
        event_factory: Function that creates the event to emit
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Execute the original function
            result = func(*args, **kwargs)
            
            # Create the event and emit it
            try:
                event = event_factory(*args, result, **kwargs)
                emit_event_safely(event)
            except Exception as e:
                logger.error(
                    f"Error emitting event after {func.__name__}: {str(e)}",
                    exc_info=True
                )
                
            return result
        return wrapper
    return decorator

def with_async_event_emission(event_factory: Callable[..., Event]) -> Callable:
    """
    Decorator that emits an event after an async function completes successfully.
    
    Similar to with_event_emission but for async functions.
    
    Args:
        event_factory: Function that creates the event to emit
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Create the event and emit it
            try:
                event = event_factory(*args, result, **kwargs)
                await emit_event_async_safely(event)
            except Exception as e:
                logger.error(
                    f"Error emitting event after async {func.__name__}: {str(e)}",
                    exc_info=True
                )
                
            return result
        return wrapper
    return decorator 