"""
Event dispatcher for the event-driven architecture.

This module contains the central event dispatcher that manages event subscriptions
and handles the distribution of events to their respective handlers.
"""

from typing import Dict, List, Callable, Any, Set, Optional, Union, Tuple
import asyncio
import logging
import inspect
import time
import traceback
from contextlib import contextmanager
from functools import wraps
import random
from datetime import datetime, timedelta

from .base import Event
from .exceptions import EventHandlerError, EventDispatchError, EventRetryError
from .persistence import event_store
from app.core.error_handling import handle_exceptions

logger = logging.getLogger(__name__)

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
DEFAULT_RETRY_BACKOFF = 2.0  # exponential backoff multiplier

# Event persistence flag - determines if events should be stored persistently
# Can be configured based on environment
PERSIST_EVENTS = True

# Metrics tracking 
class EventMetrics:
    """Tracks metrics for event processing."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.processed_events: Dict[str, int] = {}
        self.failed_events: Dict[str, int] = {}
        self.processing_times: Dict[str, List[float]] = {}
        self.handler_errors: Dict[str, Dict[str, int]] = {}
        self.retry_attempts: Dict[str, int] = {}
        self.retry_success: Dict[str, int] = {}
        self.retry_failure: Dict[str, int] = {}
    
    def record_processed_event(self, event_type: str) -> None:
        """Record a processed event."""
        if event_type not in self.processed_events:
            self.processed_events[event_type] = 0
        self.processed_events[event_type] += 1
    
    def record_failed_event(self, event_type: str) -> None:
        """Record a failed event."""
        if event_type not in self.failed_events:
            self.failed_events[event_type] = 0
        self.failed_events[event_type] += 1
    
    def record_processing_time(self, event_type: str, duration: float) -> None:
        """Record processing time for an event."""
        if event_type not in self.processing_times:
            self.processing_times[event_type] = []
        self.processing_times[event_type].append(duration)
    
    def record_handler_error(self, event_type: str, handler_name: str) -> None:
        """Record an error in a handler."""
        if event_type not in self.handler_errors:
            self.handler_errors[event_type] = {}
        if handler_name not in self.handler_errors[event_type]:
            self.handler_errors[event_type][handler_name] = 0
        self.handler_errors[event_type][handler_name] += 1
    
    def record_retry_attempt(self, event_type: str) -> None:
        """Record a retry attempt for an event type."""
        if event_type not in self.retry_attempts:
            self.retry_attempts[event_type] = 0
        self.retry_attempts[event_type] += 1
    
    def record_retry_success(self, event_type: str) -> None:
        """Record a successful retry for an event type."""
        if event_type not in self.retry_success:
            self.retry_success[event_type] = 0
        self.retry_success[event_type] += 1
    
    def record_retry_failure(self, event_type: str) -> None:
        """Record a failed retry for an event type."""
        if event_type not in self.retry_failure:
            self.retry_failure[event_type] = 0
        self.retry_failure[event_type] += 1
    
    def get_avg_processing_time(self, event_type: str) -> Optional[float]:
        """Get average processing time for an event type."""
        if event_type in self.processing_times and self.processing_times[event_type]:
            return sum(self.processing_times[event_type]) / len(self.processing_times[event_type])
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        avg_times = {}
        for event_type in self.processing_times:
            avg_times[event_type] = self.get_avg_processing_time(event_type)
        
        return {
            "processed_events": self.processed_events,
            "failed_events": self.failed_events,
            "avg_processing_times": avg_times,
            "handler_errors": self.handler_errors,
            "retry_attempts": self.retry_attempts,
            "retry_success": self.retry_success,
            "retry_failure": self.retry_failure
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.processed_events = {}
        self.failed_events = {}
        self.processing_times = {}
        self.handler_errors = {}
        self.retry_attempts = {}
        self.retry_success = {}
        self.retry_failure = {}

# Retry handling
class RetryPolicy:
    """
    Defines the retry behavior for event handlers.
    
    This class contains the configuration for how events should be
    retried in case of handler failures.
    """
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        backoff_factor: float = DEFAULT_RETRY_BACKOFF,
        jitter: bool = True
    ):
        """
        Initialize the retry policy.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add random jitter to retry delays
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def get_next_retry_delay(self, attempt: int) -> float:
        """
        Calculate the delay for the next retry attempt.
        
        Args:
            attempt: The retry attempt number (1-based)
            
        Returns:
            Delay in seconds before the next retry
        """
        if attempt <= 0:
            return 0
            
        delay = self.retry_delay * (self.backoff_factor ** (attempt - 1))
        
        if self.jitter:
            # Add random jitter (±20%)
            jitter_multiplier = 1 + random.uniform(-0.2, 0.2)
            delay *= jitter_multiplier
            
        return delay

# Error handling decorators
def event_handler_error_wrapper(func: Callable, retry_policy: RetryPolicy = None) -> Callable:
    """
    Decorator for handling errors in event handlers with retry support.
    
    Args:
        func: The function to wrap
        retry_policy: Optional retry policy for handling retries
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(event: Event, metrics: EventMetrics = None, retry_attempt: int = 0, **kwargs):
        event_type = event.event_type
        handler_name = func.__name__
        
        try:
            result = func(event, **kwargs)
            
            # Mark event as processed in the event store if persistence is enabled
            if PERSIST_EVENTS and hasattr(event, 'metadata') and hasattr(event.metadata, 'event_id'):
                event_store.mark_event_processed(event.metadata.event_id)
                
            return result
        except Exception as e:
            # Log the error with traceback
            logger.error(
                f"Error in event handler '{handler_name}' for event type '{event_type}': {str(e)}",
                exc_info=True
            )
            
            # Record metrics if provided
            if metrics:
                metrics.record_handler_error(event_type, handler_name)
            
            # Mark event processing failure in the event store if persistence is enabled
            if PERSIST_EVENTS and hasattr(event, 'metadata') and hasattr(event.metadata, 'event_id'):
                event_store.mark_event_processed(event.metadata.event_id, error=str(e))
            
            # Check if we should retry
            if retry_policy and retry_attempt < retry_policy.max_retries:
                if metrics:
                    metrics.record_retry_attempt(event_type)
                
                next_attempt = retry_attempt + 1
                delay = retry_policy.get_next_retry_delay(next_attempt)
                
                logger.info(
                    f"Scheduling retry attempt {next_attempt}/{retry_policy.max_retries} "
                    f"for handler '{handler_name}' in {delay:.2f} seconds"
                )
                
                # Schedule the retry with exponential backoff
                try:
                    time.sleep(delay)
                    result = wrapper(event, metrics, next_attempt, **kwargs)
                    if metrics:
                        metrics.record_retry_success(event_type)
                    return result
                except Exception as retry_e:
                    if metrics:
                        metrics.record_retry_failure(event_type)
                    logger.error(
                        f"Retry attempt {next_attempt} failed for handler '{handler_name}': {str(retry_e)}",
                        exc_info=True
                    )
            
            # Wrap in our custom exception
            error = EventHandlerError(
                event_type=event_type,
                handler_name=handler_name,
                message=str(e),
                details=traceback.format_exc()
            )
            # Log the error but don't raise to allow other handlers to run
            logger.error(f"Wrapped error: {error.message}")
            return None
    
    return wrapper

async def async_event_handler_error_wrapper(func: Callable, retry_policy: RetryPolicy = None) -> Callable:
    """
    Decorator for handling errors in async event handlers with retry support.
    
    Args:
        func: The async function to wrap
        retry_policy: Optional retry policy for handling retries
        
    Returns:
        Wrapped async function
    """
    @wraps(func)
    async def wrapper(event: Event, metrics: EventMetrics = None, retry_attempt: int = 0, **kwargs):
        event_type = event.event_type
        handler_name = func.__name__
        
        try:
            result = await func(event, **kwargs)
            
            # Mark event as processed in the event store if persistence is enabled
            if PERSIST_EVENTS and hasattr(event, 'metadata') and hasattr(event.metadata, 'event_id'):
                event_store.mark_event_processed(event.metadata.event_id)
                
            return result
        except Exception as e:
            # Log the error with traceback
            logger.error(
                f"Error in async event handler '{handler_name}' for event type '{event_type}': {str(e)}",
                exc_info=True
            )
            
            # Record metrics if provided
            if metrics:
                metrics.record_handler_error(event_type, handler_name)
            
            # Mark event processing failure in the event store if persistence is enabled
            if PERSIST_EVENTS and hasattr(event, 'metadata') and hasattr(event.metadata, 'event_id'):
                event_store.mark_event_processed(event.metadata.event_id, error=str(e))
            
            # Check if we should retry
            if retry_policy and retry_attempt < retry_policy.max_retries:
                if metrics:
                    metrics.record_retry_attempt(event_type)
                
                next_attempt = retry_attempt + 1
                delay = retry_policy.get_next_retry_delay(next_attempt)
                
                logger.info(
                    f"Scheduling retry attempt {next_attempt}/{retry_policy.max_retries} "
                    f"for async handler '{handler_name}' in {delay:.2f} seconds"
                )
                
                # Schedule the retry with exponential backoff
                try:
                    await asyncio.sleep(delay)
                    result = await wrapper(event, metrics, next_attempt, **kwargs)
                    if metrics:
                        metrics.record_retry_success(event_type)
                    return result
                except Exception as retry_e:
                    if metrics:
                        metrics.record_retry_failure(event_type)
                    logger.error(
                        f"Retry attempt {next_attempt} failed for async handler '{handler_name}': {str(retry_e)}",
                        exc_info=True
                    )
            
            # Wrap in our custom exception
            error = EventHandlerError(
                event_type=event_type,
                handler_name=handler_name,
                message=str(e),
                details=traceback.format_exc()
            )
            # Log the error but don't raise to allow other handlers to run
            logger.error(f"Wrapped error: {error.message}")
            return None
    
    return wrapper

class EventDispatcher:
    """
    Central event dispatcher for the application
    
    Manages event subscriptions and distribution to event handlers.
    Support both synchronous and asynchronous event handlers.
    """
    
    def __init__(self, default_retry_policy: RetryPolicy = None):
        """
        Initialize a new event dispatcher
        
        Args:
            default_retry_policy: Default retry policy for event handlers
        """
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_subscribers: Dict[str, List[Callable]] = {}
        self._is_dispatching: bool = False
        self._event_queue: List[Event] = []
        self._subscribed_event_types: Set[str] = set()
        self.metrics = EventMetrics()
        self.default_retry_policy = default_retry_policy or RetryPolicy()
    
    def subscribe(self, event_type: str, callback: Callable[[Event], Any], retry_policy: RetryPolicy = None) -> None:
        """
        Subscribe to an event type with a synchronous callback
        
        Args:
            event_type: The type of event to subscribe to
            callback: The function to call when an event of this type is emitted
            retry_policy: Optional retry policy for this handler
        """
        # Use either the provided retry policy or the default
        retry_policy = retry_policy or self.default_retry_policy
        
        # Wrap the callback in our error handler with retry support
        wrapped_callback = event_handler_error_wrapper(callback, retry_policy)
        
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(wrapped_callback)
        self._subscribed_event_types.add(event_type)
        
        logger.debug(f"Registered handler {callback.__name__} for event type {event_type}")
    
    def subscribe_async(self, event_type: str, callback: Callable[[Event], Any], retry_policy: RetryPolicy = None) -> None:
        """
        Subscribe to an event type with an asynchronous callback
        
        Args:
            event_type: The type of event to subscribe to
            callback: The async function to call when an event of this type is emitted
            retry_policy: Optional retry policy for this handler
        """
        # Use either the provided retry policy or the default
        retry_policy = retry_policy or self.default_retry_policy
        
        # Wrap the callback in our error handler
        wrapped_callback = async_event_handler_error_wrapper(callback, retry_policy)
        
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(wrapped_callback)
        self._subscribed_event_types.add(event_type)
        
        logger.debug(f"Registered async handler {callback.__name__} for event type {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe a handler from an event type
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The function to unsubscribe
            
        Returns:
            True if the subscription was removed, False otherwise
        """
        if event_type in self._subscribers:
            # Find the wrapped callback based on its name
            for i, wrapped_cb in enumerate(self._subscribers[event_type]):
                if wrapped_cb.__name__ == callback.__name__:
                    self._subscribers[event_type].pop(i)
                    logger.debug(f"Unsubscribed handler {callback.__name__} from event type {event_type}")
                    
                    # If there are no more handlers for this event type, clean up
                    if not self._subscribers[event_type] and event_type not in self._async_subscribers:
                        self._subscribed_event_types.remove(event_type)
                    
                    return True
        
        return False
    
    def unsubscribe_async(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe an async handler from an event type
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The async function to unsubscribe
            
        Returns:
            True if the subscription was removed, False otherwise
        """
        if event_type in self._async_subscribers:
            # Find the wrapped callback based on its name
            for i, wrapped_cb in enumerate(self._async_subscribers[event_type]):
                if wrapped_cb.__name__ == callback.__name__:
                    self._async_subscribers[event_type].pop(i)
                    logger.debug(f"Unsubscribed async handler {callback.__name__} from event type {event_type}")
                    
                    # If there are no more handlers for this event type, clean up
                    if not self._async_subscribers[event_type] and event_type not in self._subscribers:
                        self._subscribed_event_types.remove(event_type)
                    
                    return True
        
        return False
    
    def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribed handlers
        
        Args:
            event: The event to emit
            
        Raises:
            EventDispatchError: If there is an error during dispatch
        """
        event_type = event.event_type
        
        # Store the event persistently if enabled
        if PERSIST_EVENTS:
            try:
                event_store.store_event(event)
            except Exception as e:
                logger.error(f"Failed to store event {event_type}: {str(e)}", exc_info=True)
        
        # If we're already dispatching events, queue this one
        if self._is_dispatching:
            self._event_queue.append(event)
            return
        
        # Get synchronous subscribers for this event type
        handlers = self._subscribers.get(event_type, [])
        
        # If no handlers are registered, log a warning
        if not handlers and event_type not in self._async_subscribers:
            logger.warning(f"No handlers registered for event type {event_type}")
            return
        
        # Set the dispatching flag to avoid recursive emission
        self._is_dispatching = True
        
        try:
            # Start timing for metrics
            start_time = time.time()
            
            # Call all handlers
            for handler in handlers:
                try:
                    handler(event, metrics=self.metrics)
                except Exception as e:
                    logger.error(f"Unhandled error in event handler: {str(e)}", exc_info=True)
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_processing_time(event_type, duration)
            self.metrics.record_processed_event(event_type)
            
            logger.debug(f"Processed event {event_type} in {duration:.3f}s")
            
            # Process any events that were queued during dispatch
            queued_events = list(self._event_queue)
            self._event_queue.clear()
            
            for queued_event in queued_events:
                self.emit(queued_event)
                
        except Exception as e:
            self.metrics.record_failed_event(event_type)
            
            error = EventDispatchError(
                event_type=event_type,
                message=f"Error dispatching event: {str(e)}",
                details=traceback.format_exc()
            )
            logger.error(f"Event dispatch error: {error.message}", exc_info=True)
            raise error
        finally:
            # Reset the dispatching flag
            self._is_dispatching = False
    
    async def emit_async(self, event: Event) -> None:
        """
        Emit an event to all subscribed async handlers
        
        Args:
            event: The event to emit
            
        Raises:
            EventDispatchError: If there is an error during dispatch
        """
        event_type = event.event_type
        
        # Store the event persistently if enabled
        if PERSIST_EVENTS:
            try:
                event_store.store_event(event)
            except Exception as e:
                logger.error(f"Failed to store event {event_type}: {str(e)}", exc_info=True)
        
        # Get synchronous and asynchronous subscribers for this event type
        sync_handlers = self._subscribers.get(event_type, [])
        async_handlers = self._async_subscribers.get(event_type, [])
        
        # If no handlers are registered, log a warning
        if not sync_handlers and not async_handlers:
            logger.warning(f"No handlers registered for event type {event_type}")
            return
        
        try:
            # Start timing for metrics
            start_time = time.time()
            
            # Call synchronous handlers
            for handler in sync_handlers:
                try:
                    handler(event, metrics=self.metrics)
                except Exception as e:
                    logger.error(f"Unhandled error in sync event handler: {str(e)}", exc_info=True)
            
            # Call asynchronous handlers
            for handler in async_handlers:
                try:
                    await handler(event, metrics=self.metrics)
                except Exception as e:
                    logger.error(f"Unhandled error in async event handler: {str(e)}", exc_info=True)
            
            # Record metrics
            duration = time.time() - start_time
            self.metrics.record_processing_time(event_type, duration)
            self.metrics.record_processed_event(event_type)
            
            logger.debug(f"Processed event {event_type} in {duration:.3f}s")
                
        except Exception as e:
            self.metrics.record_failed_event(event_type)
            
            error = EventDispatchError(
                event_type=event_type,
                message=f"Error dispatching event: {str(e)}",
                details=traceback.format_exc()
            )
            logger.error(f"Event dispatch error: {error.message}", exc_info=True)
            raise error
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all collected metrics.
        
        Returns:
            Dict of metrics data
        """
        return self.metrics.get_metrics()
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics.reset_metrics()
    
    def get_subscribed_event_types(self) -> Set[str]:
        """
        Get all event types that have subscribers.
        
        Returns:
            Set of event types
        """
        return self._subscribed_event_types
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        Check if an event type has any subscribers.
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if the event type has subscribers, False otherwise
        """
        return (
            event_type in self._subscribers and len(self._subscribers[event_type]) > 0 or
            event_type in self._async_subscribers and len(self._async_subscribers[event_type]) > 0
        )
    
    async def process_unprocessed_events(self, limit: int = 100) -> int:
        """
        Process events from the event store that haven't been processed yet.
        
        This method can be used to recover from failures by replaying
        unprocessed events.
        
        Args:
            limit: Maximum number of events to process
            
        Returns:
            Number of events processed
        """
        if not PERSIST_EVENTS:
            return 0
            
        events = event_store.get_unprocessed_events(limit)
        processed_count = 0
        
        for event in events:
            try:
                await self.emit_async(event)
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process unprocessed event {event.event_type}: {str(e)}", exc_info=True)
                
        return processed_count

# Create a singleton instance of the event dispatcher
event_dispatcher = EventDispatcher() 