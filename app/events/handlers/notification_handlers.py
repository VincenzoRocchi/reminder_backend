"""
Handlers for notification-related events.

This module contains all event handlers related to notifications.
"""

import logging

from app.events.dispatcher import event_dispatcher
from app.events.definitions import (
    NotificationScheduledEvent,
    NotificationSentEvent,
    NotificationFailedEvent,
    NotificationCancelledEvent
)

logger = logging.getLogger(__name__)

# Handler functions

def handle_notification_scheduled(event: NotificationScheduledEvent) -> None:
    """
    Handle a notification scheduled event
    
    This handler is called when a notification is scheduled. It can be used
    to perform additional actions such as logging or analytics.
    
    Args:
        event: The notification scheduled event
    """
    logger.info(
        f"Notification scheduled: id={event.payload.notification_id}, "
        f"type={event.payload.notification_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

def handle_notification_sent(event: NotificationSentEvent) -> None:
    """
    Handle a notification sent event
    
    This handler is called when a notification is successfully sent. It can
    be used to update statistics, perform logging, or trigger follow-up actions.
    
    Args:
        event: The notification sent event
    """
    logger.info(
        f"Notification sent: id={event.payload.notification_id}, "
        f"type={event.payload.notification_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

def handle_notification_failed(event: NotificationFailedEvent) -> None:
    """
    Handle a notification failed event
    
    This handler is called when a notification fails to send. It can be used
    to schedule retries, alert administrators, or update statistics.
    
    Args:
        event: The notification failed event
    """
    logger.warning(
        f"Notification failed: id={event.payload.notification_id}, "
        f"type={event.payload.notification_type}, user_id={event.payload.user_id}, "
        f"error={event.payload.error_message}"
    )
    
    # Additional processing can be added here
    # For example: retry logic, alerting, etc.

def handle_notification_cancelled(event: NotificationCancelledEvent) -> None:
    """
    Handle a notification cancelled event
    
    This handler is called when a notification is cancelled. It can be used
    to update statistics or perform cleanup.
    
    Args:
        event: The notification cancelled event
    """
    logger.info(
        f"Notification cancelled: id={event.payload.notification_id}, "
        f"type={event.payload.notification_type}, user_id={event.payload.user_id}"
    )
    
    # Additional processing can be added here

# Register all notification handlers with the event dispatcher
def register_handlers():
    """Register all notification handlers with the event dispatcher"""
    event_dispatcher.subscribe(NotificationScheduledEvent.event_type, handle_notification_scheduled)
    event_dispatcher.subscribe(NotificationSentEvent.event_type, handle_notification_sent)
    event_dispatcher.subscribe(NotificationFailedEvent.event_type, handle_notification_failed)
    event_dispatcher.subscribe(NotificationCancelledEvent.event_type, handle_notification_cancelled) 