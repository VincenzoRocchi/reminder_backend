"""
Email configuration-related event definitions.

This module contains event definitions for all email configuration-related events
in the system, such as creating, updating, or deleting email configurations.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.events.base import Event, EventMetadata

# Data models for event payloads
class EmailConfigurationData(BaseModel):
    """Base data model for email configuration event payloads"""
    email_configuration_id: int
    user_id: int
    configuration_name: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    sender_email: Optional[str] = None
    is_default: Optional[bool] = None

class EmailConfigurationCreatedEvent(Event[EmailConfigurationData]):
    """Event emitted when a new email configuration is created"""
    event_type: str = "email_configuration.created"

class EmailConfigurationUpdatedEvent(Event[EmailConfigurationData]):
    """Event emitted when an email configuration is updated"""
    event_type: str = "email_configuration.updated"

class EmailConfigurationDeletedEvent(Event[EmailConfigurationData]):
    """Event emitted when an email configuration is deleted"""
    event_type: str = "email_configuration.deleted"

class EmailConfigurationSetDefaultEvent(Event[EmailConfigurationData]):
    """Event emitted when an email configuration is set as default"""
    event_type: str = "email_configuration.set_default"

# Factory functions for creating events with convenience
def create_email_configuration_created_event(
    email_configuration_id: int,
    user_id: int,
    configuration_name: str,
    smtp_server: str,
    smtp_port: int,
    sender_email: str,
    is_default: bool = False,
    metadata: Optional[EventMetadata] = None
) -> EmailConfigurationCreatedEvent:
    """
    Create an EmailConfigurationCreatedEvent with the given data
    
    Args:
        email_configuration_id: ID of the created email configuration
        user_id: ID of the user who created the email configuration
        configuration_name: Name of the email configuration
        smtp_server: SMTP server address
        smtp_port: SMTP server port
        sender_email: Sender email address
        is_default: Whether this is the default configuration
        metadata: Optional event metadata
        
    Returns:
        EmailConfigurationCreatedEvent instance
    """
    payload = EmailConfigurationData(
        email_configuration_id=email_configuration_id,
        user_id=user_id,
        configuration_name=configuration_name,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        is_default=is_default
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return EmailConfigurationCreatedEvent(payload=payload, metadata=metadata)

def create_email_configuration_updated_event(
    email_configuration_id: int,
    user_id: int,
    configuration_name: Optional[str] = None,
    smtp_server: Optional[str] = None,
    smtp_port: Optional[int] = None,
    sender_email: Optional[str] = None,
    is_default: Optional[bool] = None,
    metadata: Optional[EventMetadata] = None
) -> EmailConfigurationUpdatedEvent:
    """
    Create an EmailConfigurationUpdatedEvent with the given data
    
    Args:
        email_configuration_id: ID of the updated email configuration
        user_id: ID of the user who updated the email configuration
        configuration_name: Optional updated name of the email configuration
        smtp_server: Optional updated SMTP server address
        smtp_port: Optional updated SMTP server port
        sender_email: Optional updated sender email address
        is_default: Optional updated default status
        metadata: Optional event metadata
        
    Returns:
        EmailConfigurationUpdatedEvent instance
    """
    payload = EmailConfigurationData(
        email_configuration_id=email_configuration_id,
        user_id=user_id,
        configuration_name=configuration_name,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        is_default=is_default
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return EmailConfigurationUpdatedEvent(payload=payload, metadata=metadata)

def create_email_configuration_deleted_event(
    email_configuration_id: int,
    user_id: int,
    configuration_name: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> EmailConfigurationDeletedEvent:
    """
    Create an EmailConfigurationDeletedEvent with the given data
    
    Args:
        email_configuration_id: ID of the deleted email configuration
        user_id: ID of the user who deleted the email configuration
        configuration_name: Optional name of the deleted configuration for easier identification
        metadata: Optional event metadata
        
    Returns:
        EmailConfigurationDeletedEvent instance
    """
    payload = EmailConfigurationData(
        email_configuration_id=email_configuration_id,
        user_id=user_id,
        configuration_name=configuration_name
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return EmailConfigurationDeletedEvent(payload=payload, metadata=metadata)

def create_email_configuration_set_default_event(
    email_configuration_id: int,
    user_id: int,
    configuration_name: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> EmailConfigurationSetDefaultEvent:
    """
    Create an EmailConfigurationSetDefaultEvent with the given data
    
    Args:
        email_configuration_id: ID of the email configuration set as default
        user_id: ID of the user who set the configuration as default
        configuration_name: Optional name of the configuration for easier identification
        metadata: Optional event metadata
        
    Returns:
        EmailConfigurationSetDefaultEvent instance
    """
    payload = EmailConfigurationData(
        email_configuration_id=email_configuration_id,
        user_id=user_id,
        configuration_name=configuration_name,
        is_default=True
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return EmailConfigurationSetDefaultEvent(payload=payload, metadata=metadata) 