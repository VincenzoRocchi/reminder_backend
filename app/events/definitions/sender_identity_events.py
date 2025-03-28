"""
Sender identity related event definitions.

This module contains event definitions for all sender identity related events
in the system, such as creation, verification, and setting default identities.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.events.base import Event, EventMetadata

# Data models for event payloads
class SenderIdentityData(BaseModel):
    """Base data model for sender identity event payloads"""
    identity_id: int
    user_id: int
    identity_type: str  # EMAIL, PHONE, WHATSAPP
    value: str  # The email address or phone number
    display_name: Optional[str] = None
    is_verified: Optional[bool] = None
    is_default: Optional[bool] = None
    email_configuration_id: Optional[int] = None

# Event creation functions
def create_sender_identity_created_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str = "",
    is_verified: bool = False,
    is_default: bool = False,
    email_configuration_id: Optional[int] = None
) -> Event:
    """
    Create an event for a new sender identity being created.
    
    Args:
        identity_id: ID of the sender identity
        user_id: User ID
        identity_type: Type of identity (EMAIL, PHONE, WHATSAPP)
        value: The email address or phone number
        display_name: How it appears to recipients
        is_verified: Whether the identity is verified
        is_default: Whether it's the default for its type
        email_configuration_id: ID of associated email configuration (for EMAIL type)
        
    Returns:
        Event: The created event
    """
    return Event(
        event_type="sender_identity.created",
        metadata=EventMetadata(
            user_id=user_id,
            entity_id=identity_id,
            entity_type="sender_identity"
        ),
        payload=SenderIdentityData(
            identity_id=identity_id,
            user_id=user_id,
            identity_type=identity_type,
            value=value,
            display_name=display_name,
            is_verified=is_verified,
            is_default=is_default,
            email_configuration_id=email_configuration_id
        )
    )

def create_sender_identity_updated_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str = "",
    is_verified: bool = False,
    is_default: bool = False,
    email_configuration_id: Optional[int] = None
) -> Event:
    """
    Create an event for a sender identity being updated.
    
    Args:
        identity_id: ID of the sender identity
        user_id: User ID
        identity_type: Type of identity (EMAIL, PHONE, WHATSAPP)
        value: The email address or phone number
        display_name: How it appears to recipients
        is_verified: Whether the identity is verified
        is_default: Whether it's the default for its type
        email_configuration_id: ID of associated email configuration (for EMAIL type)
        
    Returns:
        Event: The created event
    """
    return Event(
        event_type="sender_identity.updated",
        metadata=EventMetadata(
            user_id=user_id,
            entity_id=identity_id,
            entity_type="sender_identity"
        ),
        payload=SenderIdentityData(
            identity_id=identity_id,
            user_id=user_id,
            identity_type=identity_type,
            value=value,
            display_name=display_name,
            is_verified=is_verified,
            is_default=is_default,
            email_configuration_id=email_configuration_id
        )
    )

def create_sender_identity_deleted_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str = ""
) -> Event:
    """
    Create an event for a sender identity being deleted.
    
    Args:
        identity_id: ID of the sender identity
        user_id: User ID
        identity_type: Type of identity (EMAIL, PHONE, WHATSAPP)
        value: The email address or phone number
        display_name: How it appears to recipients
        
    Returns:
        Event: The created event
    """
    return Event(
        event_type="sender_identity.deleted",
        metadata=EventMetadata(
            user_id=user_id,
            entity_id=identity_id,
            entity_type="sender_identity"
        ),
        payload=SenderIdentityData(
            identity_id=identity_id,
            user_id=user_id,
            identity_type=identity_type,
            value=value,
            display_name=display_name
        )
    )

def create_sender_identity_verified_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str = ""
) -> Event:
    """
    Create an event for a sender identity being verified.
    
    Args:
        identity_id: ID of the sender identity
        user_id: User ID
        identity_type: Type of identity (EMAIL, PHONE, WHATSAPP)
        value: The email address or phone number
        display_name: How it appears to recipients
        
    Returns:
        Event: The created event
    """
    return Event(
        event_type="sender_identity.verified",
        metadata=EventMetadata(
            user_id=user_id,
            entity_id=identity_id,
            entity_type="sender_identity"
        ),
        payload=SenderIdentityData(
            identity_id=identity_id,
            user_id=user_id,
            identity_type=identity_type,
            value=value,
            display_name=display_name,
            is_verified=True
        )
    )

def create_default_sender_identity_set_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str = ""
) -> Event:
    """
    Create an event for a sender identity being set as default.
    
    Args:
        identity_id: ID of the sender identity
        user_id: User ID
        identity_type: Type of identity (EMAIL, PHONE, WHATSAPP)
        value: The email address or phone number
        display_name: How it appears to recipients
        
    Returns:
        Event: The created event
    """
    return Event(
        event_type="sender_identity.default_set",
        metadata=EventMetadata(
            user_id=user_id,
            entity_id=identity_id,
            entity_type="sender_identity"
        ),
        payload=SenderIdentityData(
            identity_id=identity_id,
            user_id=user_id,
            identity_type=identity_type,
            value=value,
            display_name=display_name,
            is_default=True
        )
    ) 