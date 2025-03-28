"""
Handlers for client-related events.

This module contains all event handlers related to client operations.
"""

import logging

from app.events.dispatcher import event_dispatcher
from app.events.definitions import (
    ClientCreatedEvent,
    ClientUpdatedEvent,
    ClientDeletedEvent,
    ClientAddedToReminderEvent,
    ClientRemovedFromReminderEvent
)

logger = logging.getLogger(__name__)

# Handler functions

def handle_client_created(event: ClientCreatedEvent) -> None:
    """
    Handle a client created event
    
    This handler is called when a new client is created. It can be used
    to update statistics, perform logging, or trigger follow-up actions.
    
    Args:
        event: The client created event
    """
    logger.info(
        f"Client created: id={event.payload.client_id}, "
        f"name={event.payload.name}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

def handle_client_updated(event: ClientUpdatedEvent) -> None:
    """
    Handle a client updated event
    
    This handler is called when a client is updated. It can be used
    to perform logging, update related resources, or trigger notifications.
    
    Args:
        event: The client updated event
    """
    logger.info(
        f"Client updated: id={event.payload.client_id}, "
        f"user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

def handle_client_deleted(event: ClientDeletedEvent) -> None:
    """
    Handle a client deleted event
    
    This handler is called when a client is deleted. It can be used
    to perform cleanup actions, update statistics, or trigger notifications.
    
    Args:
        event: The client deleted event
    """
    logger.info(
        f"Client deleted: id={event.payload.client_id}, "
        f"user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, archive client data or clean up related records

def handle_client_added_to_reminder(event: ClientAddedToReminderEvent) -> None:
    """
    Handle a client added to reminder event
    
    This handler is called when a client is added to a reminder. It can be used
    to update statistics, perform logging, or generate additional notifications.
    
    Args:
        event: The client added to reminder event
    """
    logger.info(
        f"Client added to reminder: client_id={event.payload.client_id}, "
        f"reminder_id={event.payload.reminder_id}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

def handle_client_removed_from_reminder(event: ClientRemovedFromReminderEvent) -> None:
    """
    Handle a client removed from reminder event
    
    This handler is called when a client is removed from a reminder. It can be used
    to update statistics, perform logging, or cancel pending notifications.
    
    Args:
        event: The client removed from reminder event
    """
    logger.info(
        f"Client removed from reminder: client_id={event.payload.client_id}, "
        f"reminder_id={event.payload.reminder_id}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, cancel any pending notifications for this client and reminder

# Register all client handlers with the event dispatcher
def register_handlers():
    """Register all client handlers with the event dispatcher"""
    event_dispatcher.subscribe("client.created", handle_client_created)
    event_dispatcher.subscribe("client.updated", handle_client_updated)
    event_dispatcher.subscribe("client.deleted", handle_client_deleted)
    event_dispatcher.subscribe("client.added_to_reminder", handle_client_added_to_reminder)
    event_dispatcher.subscribe("client.removed_from_reminder", handle_client_removed_from_reminder) 