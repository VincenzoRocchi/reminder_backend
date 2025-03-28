"""
Event definitions for the application.

This package contains the definitions of all events used in the application,
organized by domain.
"""

from .reminder_events import *
from .notification_events import *
from .client_events import *
from .sender_identity_events import *
from .user_events import *

__all__ = [
    # Reminder events
    "ReminderCreatedEvent",
    "ReminderUpdatedEvent",
    "ReminderDeletedEvent",
    "ReminderDueEvent",
    
    # Notification events
    "NotificationScheduledEvent",
    "NotificationSentEvent",
    "NotificationFailedEvent",
    "NotificationCancelledEvent",
    
    # Client events
    "ClientAddedToReminderEvent",
    "ClientRemovedFromReminderEvent",
    
    # Sender identity events
    "SenderIdentityCreatedEvent",
    "SenderIdentityUpdatedEvent",
    "SenderIdentityDeletedEvent", 
    "SenderIdentityVerifiedEvent",
    "DefaultSenderIdentitySetEvent",

    # User events
    "UserData",
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
] 