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

from .base import Event
from .exceptions import EventHandlerError, EventDispatchError
from app.core.error_handling import handle_exceptions

logger = logging.getLogger(__name__)

# Metrics tracking 
class EventMetrics:
    """Tracks metrics for event processing."""
    
    def __init__(self):
        """Initialize metrics tracking."""
        self.processed_events: Dict[str, int] = {}
        self.failed_events: Dict[str, int] = {}
        self.processing_times: Dict[str, List[float]] = {}
        self.handler_errors: Dict[str, Dict[str, int]] = {}
    
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
            "handler_errors": self.handler_errors
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.processed_events = {}
        self.failed_events = {}
        self.processing_times = {}
        self.handler_errors = {}

# Error handling decorators
def event_handler_error_wrapper(func: Callable) -> Callable:
    """
    Decorator for handling errors in event handlers and maintaining metrics.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(func)
    def wrapper(event: Event, metrics: EventMetrics = None):
        event_type = event.event_type
        handler_name = func.__name__
        
        try:
            return func(event)
        except Exception as e:
            # Log the error with traceback
            logger.error(
                f"Error in event handler '{handler_name}' for event type '{event_type}': {str(e)}",
                exc_info=True
            )
            
            # Record metrics if provided
            if metrics:
                metrics.record_handler_error(event_type, handler_name)
            
            # Don't raise - we want to continue processing other handlers
            # But we do wrap it in our custom exception
            error = EventHandlerError(
                event_type=event_type,
                handler_name=handler_name,
                message=str(e),
                details=traceback.format_exc()
            )
            # Just log the error object but don't raise
            logger.error(f"Wrapped error: {error.message}")
    
    return wrapper

async def async_event_handler_error_wrapper(func: Callable) -> Callable:
    """
    Decorator for handling errors in async event handlers and maintaining metrics.
    
    Args:
        func: The async function to wrap
        
    Returns:
        Wrapped async function
    """
    @wraps(func)
    async def wrapper(event: Event, metrics: EventMetrics = None):
        event_type = event.event_type
        handler_name = func.__name__
        
        try:
            return await func(event)
        except Exception as e:
            # Log the error with traceback
            logger.error(
                f"Error in async event handler '{handler_name}' for event type '{event_type}': {str(e)}",
                exc_info=True
            )
            
            # Record metrics if provided
            if metrics:
                metrics.record_handler_error(event_type, handler_name)
            
            # Don't raise - we want to continue processing other handlers
            # But we do wrap it in our custom exception
            error = EventHandlerError(
                event_type=event_type,
                handler_name=handler_name,
                message=str(e),
                details=traceback.format_exc()
            )
            # Just log the error object but don't raise
            logger.error(f"Wrapped error: {error.message}")
    
    return wrapper

class EventDispatcher:
    """
    Central event dispatcher for the application
    
    Manages event subscriptions and distribution to event handlers.
    Support both synchronous and asynchronous event handlers.
    """
    
    def __init__(self):
        """Initialize a new event dispatcher"""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_subscribers: Dict[str, List[Callable]] = {}
        self._is_dispatching: bool = False
        self._event_queue: List[Event] = []
        self._subscribed_event_types: Set[str] = set()
        self.metrics = EventMetrics()
    
    def subscribe(self, event_type: str, callback: Callable[[Event], Any]) -> None:
        """
        Subscribe to an event type with a synchronous callback
        
        Args:
            event_type: The type of event to subscribe to
            callback: The function to call when an event of this type is emitted
        """
        # Wrap the callback in our error handler
        wrapped_callback = event_handler_error_wrapper(callback)
        
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(wrapped_callback)
        self._subscribed_event_types.add(event_type)
        logger.debug(f"Subscribed to {event_type} with {callback.__name__}")
    
    def subscribe_async(self, event_type: str, callback: Callable[[Event], Any]) -> None:
        """
        Subscribe to an event type with an asynchronous callback
        
        Args:
            event_type: The type of event to subscribe to
            callback: The async function to call when an event of this type is emitted
        """
        if not inspect.iscoroutinefunction(callback):
            raise ValueError(f"Callback {callback.__name__} must be an async function")
        
        # Wrap the callback in our async error handler
        wrapped_callback = async_event_handler_error_wrapper(callback)
            
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = []
        self._async_subscribers[event_type].append(wrapped_callback)
        self._subscribed_event_types.add(event_type)
        logger.debug(f"Subscribed async to {event_type} with {callback.__name__}")
    
    @handle_exceptions(error_message="Event dispatch failed")
    def emit(self, event: Event) -> None:
        """
        Emit an event to all subscribers
        
        Args:
            event: The event to emit
        """
        event_type = event.event_type
        logger.debug(f"Emitting event: {event}")
        
        # Queue the event if we're already dispatching
        if self._is_dispatching:
            self._event_queue.append(event)
            return
            
        with self._dispatching():
            try:
                start_time = time.time()
                self._process_event(event)
                processing_time = time.time() - start_time
                
                # Record metrics
                self.metrics.record_processed_event(event_type)
                self.metrics.record_processing_time(event_type, processing_time)
                
                # Process any queued events
                while self._event_queue:
                    next_event = self._event_queue.pop(0)
                    
                    try:
                        start_time = time.time()
                        self._process_event(next_event)
                        processing_time = time.time() - start_time
                        
                        # Record metrics
                        next_event_type = next_event.event_type
                        self.metrics.record_processed_event(next_event_type)
                        self.metrics.record_processing_time(next_event_type, processing_time)
                    except Exception as e:
                        # Record failure in metrics
                        self.metrics.record_failed_event(next_event.event_type)
                        
                        # Log but continue processing other events
                        logger.error(
                            f"Error processing queued event {next_event.event_type}: {str(e)}",
                            exc_info=True
                        )
            except Exception as e:
                # Record failure in metrics
                self.metrics.record_failed_event(event_type)
                
                # Wrap in our custom exception
                error = EventDispatchError(
                    event_type=event_type,
                    message=f"Failed to dispatch event: {str(e)}",
                    details=traceback.format_exc()
                )
                raise error
    
    def _process_event(self, event: Event) -> None:
        """
        Process a single event by calling all subscribers
        
        Args:
            event: The event to process
        """
        event_type = event.event_type
        
        # Skip if no subscribers for this event type
        if event_type not in self._subscribed_event_types:
            logger.debug(f"No subscribers for event type: {event_type}")
            return
        
        # Process synchronous subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event, self.metrics)
        
        # Process asynchronous subscribers
        if event_type in self._async_subscribers:
            for callback in self._async_subscribers[event_type]:
                asyncio.create_task(self._call_async_handler(callback, event))
    
    async def _call_async_handler(self, callback: Callable, event: Event) -> None:
        """
        Helper to call async event handlers
        
        Args:
            callback: The async function to call
            event: The event to pass to the callback
        """
        await callback(event, self.metrics)
            
    async def emit_async(self, event: Event) -> None:
        """
        Emit an event asynchronously and wait for all async handlers to complete
        
        Args:
            event: The event to emit
        """
        event_type = event.event_type
        logger.debug(f"Emitting async event: {event}")
        
        start_time = time.time()
        
        try:
            self.emit(event)  # Handle sync subscribers
            
            # Wait for async subscribers to complete
            if event_type in self._async_subscribers:
                tasks = []
                for callback in self._async_subscribers[event_type]:
                    tasks.append(callback(event, self.metrics))
                    
                if tasks:
                    await asyncio.gather(*tasks)
            
            # Record success metrics
            processing_time = time.time() - start_time
            self.metrics.record_processed_event(event_type)
            self.metrics.record_processing_time(event_type, processing_time)
            
        except Exception as e:
            # Record failure metrics
            self.metrics.record_failed_event(event_type)
            
            # Log and raise wrapped exception
            logger.error(f"Error in async event emission for {event_type}: {str(e)}", exc_info=True)
            error = EventDispatchError(
                event_type=event_type,
                message=f"Failed to emit event asynchronously: {str(e)}",
                details=traceback.format_exc()
            )
            raise error
    
    @contextmanager
    def _dispatching(self):
        """
        Context manager to track when we're dispatching events
        
        This prevents infinite loops by queuing nested event emissions
        """
        self._is_dispatching = True
        try:
            yield
        finally:
            self._is_dispatching = False
    
    def has_subscribers(self, event_type: str) -> bool:
        """
        Check if an event type has any subscribers
        
        Args:
            event_type: The event type to check
            
        Returns:
            True if there are subscribers, False otherwise
        """
        return event_type in self._subscribed_event_types
    
    def get_subscription_info(self) -> Dict[str, Dict[str, int]]:
        """
        Get information about all subscriptions
        
        Returns:
            Dictionary with event types and number of subscribers
        """
        return {
            "sync": {k: len(v) for k, v in self._subscribers.items()},
            "async": {k: len(v) for k, v in self._async_subscribers.items()}
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for event processing
        
        Returns:
            Dictionary with event metrics
        """
        return self.metrics.get_metrics()
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics
        """
        self.metrics.reset_metrics()


# Global dispatcher instance
event_dispatcher = EventDispatcher() 