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
    identity_type: str  # EMAIL, PHONE
    value: str  # The email address or phone number
    display_name: Optional[str] = None
    is_verified: Optional[bool] = None
    is_default: Optional[bool] = None

class SenderIdentityCreatedEvent(Event[SenderIdentityData]):
    """Event emitted when a new sender identity is created"""
    event_type: str = "sender_identity.created"

class SenderIdentityUpdatedEvent(Event[SenderIdentityData]):
    """Event emitted when a sender identity is updated"""
    event_type: str = "sender_identity.updated"

class SenderIdentityDeletedEvent(Event[SenderIdentityData]):
    """Event emitted when a sender identity is deleted"""
    event_type: str = "sender_identity.deleted"

class SenderIdentityVerifiedEvent(Event[SenderIdentityData]):
    """Event emitted when a sender identity is verified"""
    event_type: str = "sender_identity.verified"

class DefaultSenderIdentitySetEvent(Event[SenderIdentityData]):
    """Event emitted when a sender identity is set as default"""
    event_type: str = "sender_identity.default_set"

# Factory functions for creating events with convenience
def create_sender_identity_created_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str,
    is_verified: bool = False,
    is_default: bool = False,
    metadata: Optional[EventMetadata] = None
) -> SenderIdentityCreatedEvent:
    """
    Create a SenderIdentityCreatedEvent with the given data
    
    Args:
        identity_id: ID of the created sender identity
        user_id: ID of the user who owns the sender identity
        identity_type: Type of identity (EMAIL, PHONE)
        value: The email address or phone number
        display_name: The display name for the sender identity
        is_verified: Whether the identity is verified
        is_default: Whether the identity is set as default
        metadata: Optional event metadata
        
    Returns:
        SenderIdentityCreatedEvent instance
    """
    payload = SenderIdentityData(
        identity_id=identity_id,
        user_id=user_id,
        identity_type=identity_type,
        value=value,
        display_name=display_name,
        is_verified=is_verified,
        is_default=is_default
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return SenderIdentityCreatedEvent(payload=payload, metadata=metadata)

def create_sender_identity_updated_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: Optional[str] = None,
    is_verified: Optional[bool] = None,
    is_default: Optional[bool] = None,
    metadata: Optional[EventMetadata] = None
) -> SenderIdentityUpdatedEvent:
    """
    Create a SenderIdentityUpdatedEvent with the given data
    
    Args:
        identity_id: ID of the updated sender identity
        user_id: ID of the user who owns the sender identity
        identity_type: Type of identity (EMAIL, PHONE)
        value: The email address or phone number
        display_name: Optional updated display name
        is_verified: Optional updated verification status
        is_default: Optional updated default status
        metadata: Optional event metadata
        
    Returns:
        SenderIdentityUpdatedEvent instance
    """
    payload = SenderIdentityData(
        identity_id=identity_id,
        user_id=user_id,
        identity_type=identity_type,
        value=value,
        display_name=display_name,
        is_verified=is_verified,
        is_default=is_default
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return SenderIdentityUpdatedEvent(payload=payload, metadata=metadata)

def create_sender_identity_deleted_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    metadata: Optional[EventMetadata] = None
) -> SenderIdentityDeletedEvent:
    """
    Create a SenderIdentityDeletedEvent with the given data
    
    Args:
        identity_id: ID of the deleted sender identity
        user_id: ID of the user who owned the sender identity
        identity_type: Type of identity (EMAIL, PHONE)
        value: The email address or phone number
        metadata: Optional event metadata
        
    Returns:
        SenderIdentityDeletedEvent instance
    """
    payload = SenderIdentityData(
        identity_id=identity_id,
        user_id=user_id,
        identity_type=identity_type,
        value=value
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return SenderIdentityDeletedEvent(payload=payload, metadata=metadata)

def create_sender_identity_verified_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str,
    metadata: Optional[EventMetadata] = None
) -> SenderIdentityVerifiedEvent:
    """
    Create a SenderIdentityVerifiedEvent with the given data
    
    Args:
        identity_id: ID of the verified sender identity
        user_id: ID of the user who owns the sender identity
        identity_type: Type of identity (EMAIL, PHONE)
        value: The email address or phone number
        display_name: The display name for the sender identity
        metadata: Optional event metadata
        
    Returns:
        SenderIdentityVerifiedEvent instance
    """
    payload = SenderIdentityData(
        identity_id=identity_id,
        user_id=user_id,
        identity_type=identity_type,
        value=value,
        display_name=display_name,
        is_verified=True
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return SenderIdentityVerifiedEvent(payload=payload, metadata=metadata)

def create_default_sender_identity_set_event(
    identity_id: int,
    user_id: int,
    identity_type: str,
    value: str,
    display_name: str,
    metadata: Optional[EventMetadata] = None
) -> DefaultSenderIdentitySetEvent:
    """
    Create a DefaultSenderIdentitySetEvent with the given data
    
    Args:
        identity_id: ID of the sender identity set as default
        user_id: ID of the user who owns the sender identity
        identity_type: Type of identity (EMAIL, PHONE)
        value: The email address or phone number
        display_name: The display name for the sender identity
        metadata: Optional event metadata
        
    Returns:
        DefaultSenderIdentitySetEvent instance
    """
    payload = SenderIdentityData(
        identity_id=identity_id,
        user_id=user_id,
        identity_type=identity_type,
        value=value,
        display_name=display_name,
        is_default=True
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return DefaultSenderIdentitySetEvent(payload=payload, metadata=metadata) 