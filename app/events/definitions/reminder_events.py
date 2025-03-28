"""
Reminder-related event definitions.

This module contains event definitions for all reminder-related events
in the system, such as creation, updates, and due reminders.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.events.base import Event, EventMetadata

# Data models for event payloads
class ReminderData(BaseModel):
    """Base data model for reminder event payloads"""
    reminder_id: int
    user_id: int
    title: Optional[str] = None
    reminder_type: Optional[str] = None
    notification_type: Optional[str] = None
    reminder_date: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None

class ReminderCreatedEvent(Event[ReminderData]):
    """Event emitted when a new reminder is created"""
    event_type: str = "reminder.created"

class ReminderUpdatedEvent(Event[ReminderData]):
    """Event emitted when a reminder is updated"""
    event_type: str = "reminder.updated"

class ReminderDeletedEvent(Event[ReminderData]):
    """Event emitted when a reminder is deleted"""
    event_type: str = "reminder.deleted"

class ReminderDueEvent(Event[ReminderData]):
    """Event emitted when a reminder is due for processing"""
    event_type: str = "reminder.due"

# Factory functions for creating events with convenience
def create_reminder_created_event(
    reminder_id: int,
    user_id: int,
    title: str,
    reminder_type: str,
    notification_type: str,
    reminder_date: datetime,
    is_recurring: bool,
    recurrence_pattern: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ReminderCreatedEvent:
    """
    Create a ReminderCreatedEvent with the given data
    
    Args:
        reminder_id: ID of the created reminder
        user_id: ID of the user who created the reminder
        title: Title of the reminder
        reminder_type: Type of reminder (PAYMENT, DEADLINE, etc.)
        notification_type: Type of notification (EMAIL, SMS, etc.)
        reminder_date: Date when the reminder is due
        is_recurring: Whether the reminder is recurring
        recurrence_pattern: Recurrence pattern for recurring reminders
        metadata: Optional event metadata
        
    Returns:
        ReminderCreatedEvent instance
    """
    payload = ReminderData(
        reminder_id=reminder_id,
        user_id=user_id,
        title=title,
        reminder_type=reminder_type,
        notification_type=notification_type,
        reminder_date=reminder_date,
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ReminderCreatedEvent(payload=payload, metadata=metadata)

def create_reminder_updated_event(
    reminder_id: int,
    user_id: int,
    title: Optional[str] = None,
    reminder_type: Optional[str] = None,
    notification_type: Optional[str] = None,
    reminder_date: Optional[datetime] = None,
    is_recurring: Optional[bool] = None,
    recurrence_pattern: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ReminderUpdatedEvent:
    """
    Create a ReminderUpdatedEvent with the given data
    
    Args:
        reminder_id: ID of the updated reminder
        user_id: ID of the user who updated the reminder
        title: Updated title of the reminder (if changed)
        reminder_type: Updated type of reminder (if changed)
        notification_type: Updated type of notification (if changed)
        reminder_date: Updated date when the reminder is due (if changed)
        is_recurring: Updated recurring status (if changed)
        recurrence_pattern: Updated recurrence pattern (if changed)
        metadata: Optional event metadata
        
    Returns:
        ReminderUpdatedEvent instance
    """
    payload = ReminderData(
        reminder_id=reminder_id,
        user_id=user_id,
        title=title,
        reminder_type=reminder_type,
        notification_type=notification_type,
        reminder_date=reminder_date,
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ReminderUpdatedEvent(payload=payload, metadata=metadata)

def create_reminder_deleted_event(
    reminder_id: int,
    user_id: int,
    metadata: Optional[EventMetadata] = None
) -> ReminderDeletedEvent:
    """
    Create a ReminderDeletedEvent with the given data
    
    Args:
        reminder_id: ID of the deleted reminder
        user_id: ID of the user who deleted the reminder
        metadata: Optional event metadata
        
    Returns:
        ReminderDeletedEvent instance
    """
    payload = ReminderData(
        reminder_id=reminder_id,
        user_id=user_id
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ReminderDeletedEvent(payload=payload, metadata=metadata)

def create_reminder_due_event(
    reminder_id: int,
    user_id: int,
    title: str,
    reminder_type: str,
    notification_type: str,
    reminder_date: datetime,
    is_recurring: bool,
    recurrence_pattern: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> ReminderDueEvent:
    """
    Create a ReminderDueEvent with the given data
    
    Args:
        reminder_id: ID of the due reminder
        user_id: ID of the user who owns the reminder
        title: Title of the reminder
        reminder_type: Type of reminder (PAYMENT, DEADLINE, etc.)
        notification_type: Type of notification (EMAIL, SMS, etc.)
        reminder_date: Date when the reminder is due
        is_recurring: Whether the reminder is recurring
        recurrence_pattern: Recurrence pattern for recurring reminders
        metadata: Optional event metadata
        
    Returns:
        ReminderDueEvent instance
    """
    payload = ReminderData(
        reminder_id=reminder_id,
        user_id=user_id,
        title=title,
        reminder_type=reminder_type,
        notification_type=notification_type,
        reminder_date=reminder_date,
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return ReminderDueEvent(payload=payload, metadata=metadata) 