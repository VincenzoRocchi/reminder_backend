"""
Handlers for sender identity-related events.

This module contains all event handlers related to sender identity operations.
"""

import logging

from app.events.dispatcher import event_dispatcher
from app.events.definitions import (
    SenderIdentityCreatedEvent,
    SenderIdentityUpdatedEvent,
    SenderIdentityDeletedEvent,
    SenderIdentityVerifiedEvent,
    DefaultSenderIdentitySetEvent
)

logger = logging.getLogger(__name__)

# Handler functions

def handle_sender_identity_created(event: SenderIdentityCreatedEvent) -> None:
    """
    Handle a sender identity created event
    
    This handler is called when a new sender identity is created. It can be used
    to perform additional actions such as logging or verification workflows.
    
    Args:
        event: The sender identity created event
    """
    logger.info(
        f"Sender identity created: id={event.payload.identity_id}, "
        f"type={event.payload.identity_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, trigger verification processes

def handle_sender_identity_updated(event: SenderIdentityUpdatedEvent) -> None:
    """
    Handle a sender identity updated event
    
    This handler is called when a sender identity is updated. It can be used
    to perform additional actions such as logging or re-verification.
    
    Args:
        event: The sender identity updated event
    """
    logger.info(
        f"Sender identity updated: id={event.payload.identity_id}, "
        f"type={event.payload.identity_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, trigger re-verification if the address/number changed

def handle_sender_identity_deleted(event: SenderIdentityDeletedEvent) -> None:
    """
    Handle a sender identity deleted event
    
    This handler is called when a sender identity is deleted. It can be used
    to perform cleanup or update related resources.
    
    Args:
        event: The sender identity deleted event
    """
    logger.info(
        f"Sender identity deleted: id={event.payload.identity_id}, "
        f"type={event.payload.identity_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, update reminders to use a different sender identity

def handle_sender_identity_verified(event: SenderIdentityVerifiedEvent) -> None:
    """
    Handle a sender identity verified event
    
    This handler is called when a sender identity is verified. It can be used
    to update related resources or send notifications.
    
    Args:
        event: The sender identity verified event
    """
    logger.info(
        f"Sender identity verified: id={event.payload.identity_id}, "
        f"type={event.payload.identity_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, send a confirmation to the user

def handle_default_sender_identity_set(event: DefaultSenderIdentitySetEvent) -> None:
    """
    Handle a default sender identity set event
    
    This handler is called when a sender identity is set as the default. It can
    be used to update related resources or perform logging.
    
    Args:
        event: The default sender identity set event
    """
    logger.info(
        f"Default sender identity set: id={event.payload.identity_id}, "
        f"type={event.payload.identity_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, update reminders to use this sender identity by default

# Register all sender identity handlers with the event dispatcher
def register_handlers():
    """Register all sender identity handlers with the event dispatcher"""
    event_dispatcher.subscribe(SenderIdentityCreatedEvent.event_type, handle_sender_identity_created)
    event_dispatcher.subscribe(SenderIdentityUpdatedEvent.event_type, handle_sender_identity_updated)
    event_dispatcher.subscribe(SenderIdentityDeletedEvent.event_type, handle_sender_identity_deleted)
    event_dispatcher.subscribe(SenderIdentityVerifiedEvent.event_type, handle_sender_identity_verified)
    event_dispatcher.subscribe(DefaultSenderIdentitySetEvent.event_type, handle_default_sender_identity_set) 