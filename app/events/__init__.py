"""
Event system package.

This package provides a centralized event system to decouple services
and components, enhancing scalability and maintainability of the application.
"""

from app.events.dispatcher import event_dispatcher
from app.events.handlers import register_all_handlers
from app.events.utils import (
    emit_event_safely,
    emit_event_async_safely, 
    background_event_emission,
    with_event_emission,
    with_async_event_emission
)

__all__ = [
    'event_dispatcher',
    'register_all_handlers',
    'setup_event_system',
    'emit_event_safely',
    'emit_event_async_safely',
    'background_event_emission',
    'with_event_emission',
    'with_async_event_emission'
]

def setup_event_system():
    """
    Initialize the event system during application startup.
    
    This function:
    1. Registers all event handlers
    2. Sets up any required event infrastructure
    
    Returns:
        The configured event dispatcher
    """
    register_all_handlers()
    return event_dispatcher 