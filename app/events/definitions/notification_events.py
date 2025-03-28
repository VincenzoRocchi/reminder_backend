"""
Notification-related event definitions.

This module contains event definitions for all notification-related events
in the system, such as scheduling, sending, and notification status updates.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.events.base import Event, EventMetadata

# Data models for event payloads
class NotificationData(BaseModel):
    """Base data model for notification event payloads"""
    notification_id: int
    user_id: int
    reminder_id: int
    client_id: Optional[int] = None
    notification_type: Optional[str] = None  # EMAIL, SMS, WHATSAPP
    status: Optional[str] = None  # PENDING, SENT, FAILED, CANCELLED
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    message: Optional[str] = None

class NotificationScheduledEvent(Event[NotificationData]):
    """Event emitted when a notification is scheduled"""
    event_type: str = "notification.scheduled"

class NotificationSentEvent(Event[NotificationData]):
    """Event emitted when a notification is successfully sent"""
    event_type: str = "notification.sent"

class NotificationFailedEvent(Event[NotificationData]):
    """Event emitted when a notification fails to send"""
    event_type: str = "notification.failed"

class NotificationCancelledEvent(Event[NotificationData]):
    """Event emitted when a notification is cancelled"""
    event_type: str = "notification.cancelled"

# Factory functions for creating events with convenience
def create_notification_scheduled_event(
    notification_id: int,
    user_id: int,
    reminder_id: int,
    client_id: int,
    notification_type: str,
    message: Optional[str] = None,
    metadata: Optional[EventMetadata] = None
) -> NotificationScheduledEvent:
    """
    Create a NotificationScheduledEvent with the given data
    
    Args:
        notification_id: ID of the scheduled notification
        user_id: ID of the user who owns the notification
        reminder_id: ID of the associated reminder
        client_id: ID of the client receiving the notification
        notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
        message: Optional message content
        metadata: Optional event metadata
        
    Returns:
        NotificationScheduledEvent instance
    """
    payload = NotificationData(
        notification_id=notification_id,
        user_id=user_id,
        reminder_id=reminder_id,
        client_id=client_id,
        notification_type=notification_type,
        status="PENDING",
        message=message
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return NotificationScheduledEvent(payload=payload, metadata=metadata)

def create_notification_sent_event(
    notification_id: int,
    user_id: int,
    reminder_id: int,
    client_id: int,
    notification_type: str,
    sent_at: datetime,
    metadata: Optional[EventMetadata] = None
) -> NotificationSentEvent:
    """
    Create a NotificationSentEvent with the given data
    
    Args:
        notification_id: ID of the sent notification
        user_id: ID of the user who owns the notification
        reminder_id: ID of the associated reminder
        client_id: ID of the client who received the notification
        notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
        sent_at: When the notification was sent
        metadata: Optional event metadata
        
    Returns:
        NotificationSentEvent instance
    """
    payload = NotificationData(
        notification_id=notification_id,
        user_id=user_id,
        reminder_id=reminder_id,
        client_id=client_id,
        notification_type=notification_type,
        status="SENT",
        sent_at=sent_at
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return NotificationSentEvent(payload=payload, metadata=metadata)

def create_notification_failed_event(
    notification_id: int,
    user_id: int,
    reminder_id: int,
    client_id: int,
    notification_type: str,
    error_message: str,
    metadata: Optional[EventMetadata] = None
) -> NotificationFailedEvent:
    """
    Create a NotificationFailedEvent with the given data
    
    Args:
        notification_id: ID of the failed notification
        user_id: ID of the user who owns the notification
        reminder_id: ID of the associated reminder
        client_id: ID of the client who should have received the notification
        notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
        error_message: Error message describing the failure
        metadata: Optional event metadata
        
    Returns:
        NotificationFailedEvent instance
    """
    payload = NotificationData(
        notification_id=notification_id,
        user_id=user_id,
        reminder_id=reminder_id,
        client_id=client_id,
        notification_type=notification_type,
        status="FAILED",
        error_message=error_message
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return NotificationFailedEvent(payload=payload, metadata=metadata)

def create_notification_cancelled_event(
    notification_id: int,
    user_id: int,
    reminder_id: int,
    client_id: int,
    notification_type: str,
    metadata: Optional[EventMetadata] = None
) -> NotificationCancelledEvent:
    """
    Create a NotificationCancelledEvent with the given data
    
    Args:
        notification_id: ID of the cancelled notification
        user_id: ID of the user who owns the notification
        reminder_id: ID of the associated reminder
        client_id: ID of the client who would have received the notification
        notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
        metadata: Optional event metadata
        
    Returns:
        NotificationCancelledEvent instance
    """
    payload = NotificationData(
        notification_id=notification_id,
        user_id=user_id,
        reminder_id=reminder_id,
        client_id=client_id,
        notification_type=notification_type,
        status="CANCELLED"
    )
    
    if metadata is None:
        metadata = EventMetadata(user_id=user_id)
    
    return NotificationCancelledEvent(payload=payload, metadata=metadata) 