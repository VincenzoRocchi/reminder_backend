"""
Handlers for user-related events.

This module contains all event handlers related to user operations.
"""

import logging

from app.events.dispatcher import event_dispatcher
from app.events.definitions import (
    UserCreatedEvent,
    UserUpdatedEvent,
    UserDeletedEvent
)

logger = logging.getLogger(__name__)

# Handler functions

def handle_user_created(event: UserCreatedEvent) -> None:
    """
    Handle a user created event
    
    This handler is called when a new user is created. It can be used
    to perform additional actions such as sending welcome emails,
    setting up default configs, etc.
    
    Args:
        event: The user created event
    """
    logger.info(
        f"User created: id={event.payload.user_id}, "
        f"username={event.payload.username}, email={event.payload.email}"
    )
    
    # Additional processing can be added here
    # For example:
    # - Send welcome email
    # - Set up default configurations or preferences
    # - Create default sender identities

def handle_user_updated(event: UserUpdatedEvent) -> None:
    """
    Handle a user updated event
    
    This handler is called when a user is updated. It can be used
    to perform additional actions such as logging, notifications, etc.
    
    Args:
        event: The user updated event
    """
    logger.info(
        f"User updated: id={event.payload.user_id}, "
        f"username={event.payload.username}"
    )
    
    # Additional processing can be added here
    # For example:
    # - Send notification if important fields changed
    # - Update related resources

def handle_user_deleted(event: UserDeletedEvent) -> None:
    """
    Handle a user deleted event
    
    This handler is called when a user is deleted. It can be used
    to perform cleanup actions or archiving.
    
    Args:
        event: The user deleted event
    """
    logger.info(
        f"User deleted: id={event.payload.user_id}, "
        f"username={event.payload.username}"
    )
    
    # Additional processing can be added here
    # For example:
    # - Clean up user resources
    # - Archive user data
    # - Send farewell email

# Register all user handlers with the event dispatcher
def register_handlers():
    """Register all user handlers with the event dispatcher"""
    event_dispatcher.subscribe(UserCreatedEvent.event_type, handle_user_created)
    event_dispatcher.subscribe(UserUpdatedEvent.event_type, handle_user_updated)
    event_dispatcher.subscribe(UserDeletedEvent.event_type, handle_user_deleted) 