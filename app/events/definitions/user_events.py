"""
User-related event definitions.

This module contains event definitions for all user-related events
in the system, such as user creation, updates, and deletion.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

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

class AuthData(BaseModel):
    """Base data model for authentication event payloads"""
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    success: bool = True

class UserCreatedEvent(Event[UserData]):
    """Event emitted when a new user is created"""
    event_type: str = "user.created"

class UserUpdatedEvent(Event[UserData]):
    """Event emitted when a user is updated"""
    event_type: str = "user.updated"

class UserDeletedEvent(Event[UserData]):
    """Event emitted when a user is deleted"""
    event_type: str = "user.deleted"

class UserLoggedInEvent(Event[AuthData]):
    """Event emitted when a user logs in"""
    event_type: str = "user.logged_in"

class UserLoggedOutEvent(Event[AuthData]):
    """Event emitted when a user logs out"""
    event_type: str = "user.logged_out"

class UserPasswordResetEvent(Event[AuthData]):
    """Event emitted when a user resets their password"""
    event_type: str = "user.password_reset"

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

def create_user_logged_in_event(
    user_id: int,
    username: Optional[str] = None, 
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    metadata: Optional[EventMetadata] = None
) -> UserLoggedInEvent:
    """
    Create a UserLoggedInEvent with the given data
    
    Args:
        user_id: ID of the user who logged in
        username: Optional username of the user
        email: Optional email of the user
        ip_address: Optional IP address of the request
        user_agent: Optional user agent of the request
        success: Whether the login was successful
        metadata: Optional event metadata
        
    Returns:
        UserLoggedInEvent instance
    """
    payload = AuthData(
        user_id=user_id,
        username=username,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
        success=success
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserLoggedInEvent(payload=payload, metadata=metadata)

def create_user_logged_out_event(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> UserLoggedOutEvent:
    """
    Create a UserLoggedOutEvent with the given data
    
    Args:
        user_id: ID of the user who logged out
        username: Optional username of the user
        email: Optional email of the user
        ip_address: Optional IP address of the request
        user_agent: Optional user agent of the request
        metadata: Optional event metadata
        
    Returns:
        UserLoggedOutEvent instance
    """
    payload = AuthData(
        user_id=user_id,
        username=username,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
        success=True
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserLoggedOutEvent(payload=payload, metadata=metadata)

def create_user_password_reset_event(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    metadata: Optional[EventMetadata] = None
) -> UserPasswordResetEvent:
    """
    Create a UserPasswordResetEvent with the given data
    
    Args:
        user_id: ID of the user who reset their password
        username: Optional username of the user
        email: Optional email of the user
        ip_address: Optional IP address of the request
        user_agent: Optional user agent of the request
        success: Whether the password reset was successful
        metadata: Optional event metadata
        
    Returns:
        UserPasswordResetEvent instance
    """
    payload = AuthData(
        user_id=user_id,
        username=username,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.utcnow(),
        success=success
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return UserPasswordResetEvent(payload=payload, metadata=metadata) 