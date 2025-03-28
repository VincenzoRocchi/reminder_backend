"""
Event definitions for the application.

This package contains the definitions of all events used in the application,
organized by domain.
"""

from app.events.base import Event
from .reminder_events import *
from .notification_events import *
from .client_events import *
from .sender_identity_events import (
    create_sender_identity_created_event,
    create_sender_identity_updated_event,
    create_sender_identity_deleted_event,
    create_sender_identity_verified_event,
    create_default_sender_identity_set_event
)
from .user_events import *
from .email_configuration_events import *

# Map of event types to their respective classes for dynamic loading
EVENT_TYPES = {
    # Client events
    "client.created": ClientCreatedEvent,
    "client.updated": ClientUpdatedEvent,
    "client.deleted": ClientDeletedEvent,
    "client.added_to_reminder": ClientAddedToReminderEvent,
    "client.removed_from_reminder": ClientRemovedFromReminderEvent,
    
    # Reminder events
    "reminder.created": ReminderCreatedEvent,
    "reminder.updated": ReminderUpdatedEvent,
    "reminder.deleted": ReminderDeletedEvent,
    "reminder.due_soon": ReminderDueEvent,
    "reminder.overdue": ReminderDueEvent,
    
    # Notification events
    "notification.scheduled": NotificationScheduledEvent,
    "notification.sent": NotificationSentEvent,
    "notification.delivered": NotificationSentEvent,
    "notification.failed": NotificationFailedEvent,
    "notification.cancelled": NotificationCancelledEvent,
    
    # Sender identity events
    # These now use function-based event creation
    "sender_identity.created": Event,
    "sender_identity.updated": Event,
    "sender_identity.deleted": Event,
    "sender_identity.verified": Event,
    "sender_identity.default_set": Event,
    
    # User events
    "user.created": UserCreatedEvent,
    "user.updated": UserUpdatedEvent,
    "user.deleted": UserDeletedEvent,
    "user.logged_in": UserLoggedInEvent,
    "user.logged_out": UserLoggedOutEvent,
    "user.password_reset": UserPasswordResetEvent,
    
    # Email configuration events
    "email_configuration.created": EmailConfigurationCreatedEvent,
    "email_configuration.updated": EmailConfigurationUpdatedEvent,
    "email_configuration.deleted": EmailConfigurationDeletedEvent,
    "email_configuration.set_default": EmailConfigurationSetDefaultEvent
}

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
    "ClientCreatedEvent",
    "ClientUpdatedEvent",
    "ClientDeletedEvent",
    "ClientAddedToReminderEvent",
    "ClientRemovedFromReminderEvent",
    
    # Sender identity events (function-based)
    "create_sender_identity_created_event",
    "create_sender_identity_updated_event",
    "create_sender_identity_deleted_event",
    "create_sender_identity_verified_event",
    "create_default_sender_identity_set_event",

    # User events
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
    "UserLoggedInEvent",
    "UserLoggedOutEvent",
    "UserPasswordResetEvent",
    
    # Email configuration events
    "EmailConfigurationCreatedEvent",
    "EmailConfigurationUpdatedEvent",
    "EmailConfigurationDeletedEvent",
    "EmailConfigurationSetDefaultEvent",

    # Event type mapping
    "EVENT_TYPES"
] 