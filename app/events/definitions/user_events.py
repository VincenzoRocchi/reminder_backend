"""
User-related event definitions.

This module contains event definitions for all user-related events
in the system, such as user creation, updates, and deletion.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.events.base import Event, EventMetadata

# Data models for event payloads
class UserData(BaseModel):
    """Base data model for user event payloads"""
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    business_name: Optional[str] = None

class UserCreatedEvent(Event[UserData]):
    """Event emitted when a new user is created"""
    event_type: str = "user.created"

class UserUpdatedEvent(Event[UserData]):
    """Event emitted when a user is updated"""
    event_type: str = "user.updated"

class UserDeletedEvent(Event[UserData]):
    """Event emitted when a user is deleted"""
    event_type: str = "user.deleted"

# Factory functions for creating events with convenience
def create_user_created_event(
    user_id: int,
    username: str,
    email: str,
    is_active: bool = True,
    is_superuser: bool = False,
    business_name: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> UserCreatedEvent:
    """
    Create a UserCreatedEvent with the given data
    
    Args:
        user_id: ID of the created user
        username: Username of the user
        email: Email of the user
        is_active: Whether the user is active
        is_superuser: Whether the user is a superuser
        business_name: Optional business name
        metadata: Optional event metadata
        
    Returns:
        UserCreatedEvent instance
    """
    payload = UserData(
        user_id=user_id,
        username=username,
        email=email,
        is_active=is_active,
        is_superuser=is_superuser,
        business_name=business_name
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserCreatedEvent(payload=payload, metadata=metadata)

def create_user_updated_event(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    business_name: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> UserUpdatedEvent:
    """
    Create a UserUpdatedEvent with the given data
    
    Args:
        user_id: ID of the updated user
        username: Optional updated username
        email: Optional updated email
        is_active: Optional updated active status
        is_superuser: Optional updated superuser status
        business_name: Optional updated business name
        metadata: Optional event metadata
        
    Returns:
        UserUpdatedEvent instance
    """
    payload = UserData(
        user_id=user_id,
        username=username,
        email=email,
        is_active=is_active,
        is_superuser=is_superuser,
        business_name=business_name
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserUpdatedEvent(payload=payload, metadata=metadata)

def create_user_deleted_event(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> UserDeletedEvent:
    """
    Create a UserDeletedEvent with the given data
    
    Args:
        user_id: ID of the deleted user
        username: Optional username of the deleted user
        email: Optional email of the deleted user
        metadata: Optional event metadata
        
    Returns:
        UserDeletedEvent instance
    """
    payload = UserData(
        user_id=user_id,
        username=username,
        email=email
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserDeletedEvent(payload=payload, metadata=metadata) 