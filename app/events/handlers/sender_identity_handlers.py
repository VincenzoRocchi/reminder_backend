"""
Handlers for sender identity-related events.

This module contains all event handlers related to sender identity operations.
"""

import logging
from typing import Any

from app.events.dispatcher import event_dispatcher
from app.events.base import Event

logger = logging.getLogger(__name__)

# Handler functions

def handle_sender_identity_created(event: Event) -> None:
    """
    Handle a sender identity created event
    
    This handler is called when a new sender identity is created. It can be used
    to perform additional actions such as logging or verification workflows.
    
    Args:
        event: The sender identity created event
    """
    payload = event.payload
    logger.info(
        f"Sender identity created: id={payload.identity_id}, "
        f"type={payload.identity_type}, user_id={payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, trigger verification processes

def handle_sender_identity_updated(event: Event) -> None:
    """
    Handle a sender identity updated event
    
    This handler is called when a sender identity is updated. It can be used
    to perform additional actions such as logging or verification workflows.
    
    Args:
        event: The sender identity updated event
    """
    payload = event.payload
    logger.info(
        f"Sender identity updated: id={payload.identity_id}, "
        f"type={payload.identity_type}, user_id={payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, trigger reverification if email or phone changed

def handle_sender_identity_deleted(event: Event) -> None:
    """
    Handle a sender identity deleted event
    
    This handler is called when a sender identity is deleted. It can be used
    to perform cleanup actions or logging.
    
    Args:
        event: The sender identity deleted event
    """
    payload = event.payload
    logger.info(
        f"Sender identity deleted: id={payload.identity_id}, "
        f"type={payload.identity_type}, user_id={payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, cleanup related data or notify other systems

def handle_sender_identity_verified(event: Event) -> None:
    """
    Handle a sender identity verified event
    
    This handler is called when a sender identity is verified. It can be used
    to perform additional actions such as enabling features.
    
    Args:
        event: The sender identity verified event
    """
    payload = event.payload
    logger.info(
        f"Sender identity verified: id={payload.identity_id}, "
        f"type={payload.identity_type}, user_id={payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, enable features that require verified identity

def handle_default_sender_identity_set(event: Event) -> None:
    """
    Handle a default sender identity set event
    
    This handler is called when a sender identity is set as default. It can be used
    to perform additional actions such as updating related configurations.
    
    Args:
        event: The default sender identity set event
    """
    payload = event.payload
    logger.info(
        f"Default sender identity set: id={payload.identity_id}, "
        f"type={payload.identity_type}, user_id={payload.user_id}"
    )
    
    # Additional processing can be added here
    # For example, update default settings in other services

# Register all sender identity handlers with the event dispatcher
def register_handlers():
    """Register all sender identity handlers with the event dispatcher"""
    event_dispatcher.subscribe("sender_identity.created", handle_sender_identity_created)
    event_dispatcher.subscribe("sender_identity.updated", handle_sender_identity_updated)
    event_dispatcher.subscribe("sender_identity.deleted", handle_sender_identity_deleted)
    event_dispatcher.subscribe("sender_identity.verified", handle_sender_identity_verified)
    event_dispatcher.subscribe("sender_identity.default_set", handle_default_sender_identity_set) 