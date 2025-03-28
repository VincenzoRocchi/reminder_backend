"""
Event system package.

This package provides a centralized event system to decouple services
and components, enhancing scalability and maintainability of the application.
"""

import asyncio
import logging
from typing import Optional

from app.events.dispatcher import event_dispatcher
from app.events.handlers import register_all_handlers
from app.events.persistence import event_store
from app.events.utils import (
    emit_event_safely,
    emit_event_async_safely, 
    background_event_emission,
    with_event_emission,
    with_async_event_emission,
    transactional_events,
    queue_event
)

logger = logging.getLogger(__name__)

__all__ = [
    'event_dispatcher',
    'register_all_handlers',
    'setup_event_system',
    'recover_unprocessed_events',
    'emit_event_safely',
    'emit_event_async_safely',
    'background_event_emission',
    'with_event_emission',
    'with_async_event_emission',
    'transactional_events',
    'queue_event'
]

def setup_event_system(recover_events: bool = True, recovery_limit: int = 100):
    """
    Initialize the event system during application startup.
    
    This function:
    1. Registers all event handlers
    2. Sets up any required event infrastructure
    3. Optionally recovers unprocessed events
    
    Args:
        recover_events: Whether to recover unprocessed events at startup
        recovery_limit: Maximum number of events to recover
    
    Returns:
        The configured event dispatcher
    """
    logger.info("Setting up event system...")
    
    # Register all event handlers
    register_all_handlers()
    
    # Queue recovery of unprocessed events
    if recover_events:
        asyncio.create_task(recover_unprocessed_events(limit=recovery_limit))
    
    return event_dispatcher

async def recover_unprocessed_events(limit: int = 100) -> int:
    """
    Recover and process any unprocessed events from the event store.
    
    This function should be called during application startup to ensure
    that events that were persisted but not processed (e.g., due to a
    system crash) are properly handled.
    
    Args:
        limit: Maximum number of events to recover
    
    Returns:
        Number of events processed
    """
    logger.info(f"Recovering up to {limit} unprocessed events...")
    
    try:
        count = await event_dispatcher.process_unprocessed_events(limit=limit)
        
        if count > 0:
            logger.info(f"Successfully recovered and processed {count} events")
        else:
            logger.info("No unprocessed events found")
            
        return count
    except Exception as e:
        logger.error(f"Error recovering unprocessed events: {str(e)}", exc_info=True)
        return 0 