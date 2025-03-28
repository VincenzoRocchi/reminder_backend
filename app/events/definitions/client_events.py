"""
Client-related event definitions.

This module contains event definitions for all client-related events
in the system, such as adding or removing clients from reminders.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.events.base import Event, EventMetadata

# Data models for event payloads
class ClientData(BaseModel):
    """Base data model for client event payloads"""
    client_id: int
    user_id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

class ClientReminderData(BaseModel):
    """Base data model for client-reminder relationship event payloads"""
    client_id: int
    reminder_id: int
    user_id: int
    client_name: Optional[str] = None
    reminder_title: Optional[str] = None

class ClientCreatedEvent(Event[ClientData]):
    """Event emitted when a new client is created"""
    event_type: str = "client.created"

class ClientUpdatedEvent(Event[ClientData]):
    """Event emitted when a client is updated"""
    event_type: str = "client.updated"

class ClientDeletedEvent(Event[ClientData]):
    """Event emitted when a client is deleted"""
    event_type: str = "client.deleted"

class ClientAddedToReminderEvent(Event[ClientReminderData]):
    """Event emitted when a client is added to a reminder"""
    event_type: str = "client.added_to_reminder"

class ClientRemovedFromReminderEvent(Event[ClientReminderData]):
    """Event emitted when a client is removed from a reminder"""
    event_type: str = "client.removed_from_reminder"

# Factory functions for creating events with convenience
def create_client_created_event(
    client_id: int,
    user_id: int,
    name: str,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    is_active: bool = True,
    metadata: Optional[EventMetadata] = None
) -> ClientCreatedEvent:
    """
    Create a ClientCreatedEvent with the given data
    
    Args:
        client_id: ID of the created client
        user_id: ID of the user who created the client
        name: Name of the client
        email: Optional email of the client
        phone_number: Optional phone number of the client
        is_active: Whether the client is active
        metadata: Optional event metadata
        
    Returns:
        ClientCreatedEvent instance
    """
    payload = ClientData(
        client_id=client_id,
        user_id=user_id,
        name=name,
        email=email,
        phone_number=phone_number,
        is_active=is_active
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ClientCreatedEvent(payload=payload, metadata=metadata)

def create_client_updated_event(
    client_id: int,
    user_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    is_active: Optional[bool] = None,
    metadata: Optional[EventMetadata] = None
) -> ClientUpdatedEvent:
    """
    Create a ClientUpdatedEvent with the given data
    
    Args:
        client_id: ID of the updated client
        user_id: ID of the user who updated the client
        name: Optional updated name of the client
        email: Optional updated email of the client
        phone_number: Optional updated phone number of the client
        is_active: Optional updated active status of the client
        metadata: Optional event metadata
        
    Returns:
        ClientUpdatedEvent instance
    """
    payload = ClientData(
        client_id=client_id,
        user_id=user_id,
        name=name,
        email=email,
        phone_number=phone_number,
        is_active=is_active
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ClientUpdatedEvent(payload=payload, metadata=metadata)

def create_client_deleted_event(
    client_id: int,
    user_id: int,
    name: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ClientDeletedEvent:
    """
    Create a ClientDeletedEvent with the given data
    
    Args:
        client_id: ID of the deleted client
        user_id: ID of the user who deleted the client
        name: Optional name of the deleted client for easier identification
        metadata: Optional event metadata
        
    Returns:
        ClientDeletedEvent instance
    """
    payload = ClientData(
        client_id=client_id,
        user_id=user_id,
        name=name
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ClientDeletedEvent(payload=payload, metadata=metadata)

def create_client_added_to_reminder_event(
    client_id: int,
    reminder_id: int,
    user_id: int,
    client_name: Optional[str] = None,
    reminder_title: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ClientAddedToReminderEvent:
    """
    Create a ClientAddedToReminderEvent with the given data
    
    Args:
        client_id: ID of the client added to the reminder
        reminder_id: ID of the reminder the client was added to
        user_id: ID of the user who owns both the client and reminder
        client_name: Optional name of the client for easier identification
        reminder_title: Optional title of the reminder for easier identification
        metadata: Optional event metadata
        
    Returns:
        ClientAddedToReminderEvent instance
    """
    payload = ClientReminderData(
        client_id=client_id,
        reminder_id=reminder_id,
        user_id=user_id,
        client_name=client_name,
        reminder_title=reminder_title
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ClientAddedToReminderEvent(payload=payload, metadata=metadata)

def create_client_removed_from_reminder_event(
    client_id: int,
    reminder_id: int,
    user_id: int,
    client_name: Optional[str] = None,
    reminder_title: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ClientRemovedFromReminderEvent:
    """
    Create a ClientRemovedFromReminderEvent with the given data
    
    Args:
        client_id: ID of the client removed from the reminder
        reminder_id: ID of the reminder the client was removed from
        user_id: ID of the user who owns both the client and reminder
        client_name: Optional name of the client for easier identification
        reminder_title: Optional title of the reminder for easier identification
        metadata: Optional event metadata
        
    Returns:
        ClientRemovedFromReminderEvent instance
    """
    payload = ClientReminderData(
        client_id=client_id,
        reminder_id=reminder_id,
        user_id=user_id,
        client_name=client_name,
        reminder_title=reminder_title
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ClientRemovedFromReminderEvent(payload=payload, metadata=metadata) 