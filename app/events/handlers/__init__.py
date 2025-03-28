"""
Event handlers package for the reminder system.

This package contains all event handlers organized by domain.
"""

from app.events.handlers import (
    reminder_handlers,
    notification_handlers,
    client_handlers,
    sender_identity_handlers,
    user_handlers
)

def register_all_handlers():
    """Register all event handlers with the event dispatcher."""
    reminder_handlers.register_handlers()
    notification_handlers.register_handlers()
    client_handlers.register_handlers()
    sender_identity_handlers.register_handlers()
    user_handlers.register_handlers() 