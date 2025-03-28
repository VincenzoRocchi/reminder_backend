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
    "reminder.due_soon": ReminderDueSoonEvent,
    "reminder.overdue": ReminderOverdueEvent,
    
    # Notification events
    "notification.created": NotificationCreatedEvent,
    "notification.sent": NotificationSentEvent,
    "notification.delivered": NotificationDeliveredEvent,
    "notification.failed": NotificationFailedEvent,
    
    # Sender identity events
    "sender_identity.created": SenderIdentityCreatedEvent,
    "sender_identity.updated": SenderIdentityUpdatedEvent,
    "sender_identity.deleted": SenderIdentityDeletedEvent,
    "sender_identity.verified": SenderIdentityVerifiedEvent,
    "sender_identity.rejected": SenderIdentityRejectedEvent,
    
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
    "ReminderDueSoonEvent",
    "ReminderOverdueEvent",
    
    # Notification events
    "NotificationCreatedEvent",
    "NotificationSentEvent",
    "NotificationDeliveredEvent",
    "NotificationFailedEvent",
    
    # Client events
    "ClientCreatedEvent",
    "ClientUpdatedEvent",
    "ClientDeletedEvent",
    "ClientAddedToReminderEvent",
    "ClientRemovedFromReminderEvent",
    
    # Sender identity events
    "SenderIdentityCreatedEvent",
    "SenderIdentityUpdatedEvent",
    "SenderIdentityDeletedEvent",
    "SenderIdentityVerifiedEvent",
    "SenderIdentityRejectedEvent",

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