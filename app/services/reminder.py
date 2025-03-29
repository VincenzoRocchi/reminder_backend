from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.models.reminders import Reminder
from app.schemas.reminders import (
    ReminderCreate, 
    ReminderUpdate, 
    ReminderSchema,
    ReminderDetail,
    ReminderType,
    NotificationType
)
from app.core.exceptions import (
    ReminderNotFoundError,
    ClientNotFoundError,
    InvalidConfigurationError,
    InvalidOperationError
)
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import emit_event_safely, with_event_emission
from app.events.definitions.reminder_events import (
    create_reminder_created_event,
    create_reminder_updated_event,
    create_reminder_deleted_event,
    create_reminder_due_event
)

# Event factory functions for decorators
def make_reminder_created_event(service, db, reminder_in, user_id, result):
    """
    Create a reminder created event.
    
    Args:
        service: The service instance
        db: Database session
        reminder_in: Reminder creation schema
        user_id: User ID
        result: Created reminder (function result)
        
    Returns:
        Event for reminder created
    """
    return create_reminder_created_event(
        reminder_id=result.id,
        user_id=result.user_id,
        title=result.title,
        reminder_type=result.reminder_type,
        notification_type=result.notification_type,
        reminder_date=result.reminder_date,
        is_recurring=result.is_recurring,
        recurrence_pattern=result.recurrence_pattern
    )

def make_reminder_updated_event(service, db, reminder_id, reminder_in, user_id, result):
    """
    Create a reminder updated event.
    
    Args:
        service: The service instance
        db: Database session
        reminder_id: Reminder ID
        reminder_in: Reminder update schema
        user_id: User ID
        result: Updated reminder (function result)
        
    Returns:
        Event for reminder updated
    """
    return create_reminder_updated_event(
        reminder_id=result.id,
        user_id=result.user_id,
        title=result.title,
        reminder_type=result.reminder_type,
        notification_type=result.notification_type,
        reminder_date=result.reminder_date,
        is_recurring=result.is_recurring,
        recurrence_pattern=result.recurrence_pattern
    )

def make_reminder_deleted_event(service, db, reminder_id, user_id, result):
    """
    Create a reminder deleted event.
    
    Args:
        service: The service instance
        db: Database session
        reminder_id: Reminder ID
        user_id: User ID
        result: Deleted reminder (function result)
        
    Returns:
        Event for reminder deleted
    """
    return create_reminder_deleted_event(
        reminder_id=reminder_id,
        user_id=user_id,
        title=result.title
    )

class ReminderService:
    """
    Service layer for Reminder operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = reminder_repository
        self.client_repository = client_repository
    
    @handle_exceptions(error_message="Failed to get reminder")
    def get_reminder(self, db: Session, *, reminder_id: int, user_id: int) -> Reminder:
        """
        Get a reminder by ID.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            
        Returns:
            Reminder: Reminder object
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.repository.get(db, id=reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
        return reminder
    
    @handle_exceptions(error_message="Failed to get reminders by user ID")
    def get_reminders_by_user_id(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Reminder]:
        """
        Get all reminders for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        return self.repository.get_by_user_id(
            db, 
            user_id=user_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
    
    @handle_exceptions(error_message="Failed to get reminders by client ID")
    def get_reminders_by_client_id(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Reminder]:
        """
        Get all reminders for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_inactive: Whether to include inactive reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        # Verify the client belongs to the user
        client = self.client_repository.get(db, id=client_id)
        if not client or client.user_id != user_id:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
            
        return self.repository.get_by_client_id(
            db, 
            client_id=client_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create reminder")
    @with_event_emission(make_reminder_created_event)
    def create_reminder(
        self, 
        db: Session, 
        *, 
        reminder_in: ReminderCreate, 
        user_id: int
    ) -> Reminder:
        """
        Create a new reminder.
        
        Args:
            db: Database session
            reminder_in: Reminder creation schema
            user_id: User ID
            
        Returns:
            Reminder: Created reminder
            
        Raises:
            ClientNotFoundError: If client not found
            InvalidConfigurationError: If reminder configuration is invalid
        """
        # Validate client exists and belongs to user
        if hasattr(reminder_in, 'client_ids') and reminder_in.client_ids:
            for client_id in reminder_in.client_ids:
                client = self.client_repository.get(db, id=client_id)
                if not client or client.user_id != user_id:
                    raise ClientNotFoundError(f"Client with ID {client_id} not found")
        elif hasattr(reminder_in, 'client_id') and reminder_in.client_id:
            client = self.client_repository.get(db, id=reminder_in.client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {reminder_in.client_id} not found")
        
        # Validate reminder configuration
        if reminder_in.is_recurring and not reminder_in.recurrence_pattern:
            raise InvalidConfigurationError("Recurring reminders must have a recurrence pattern")
        
        # Get the sender identity to validate notification type compatibility
        from app.services.senderIdentity import sender_identity_service
        from app.models.senderIdentities import IdentityTypeEnum
        
        sender_identity = sender_identity_service.get_sender_identity(
            db, 
            sender_identity_id=reminder_in.sender_identity_id, 
            user_id=user_id
        )
        
        # Validate sender identity is complete
        if not sender_identity.is_complete:
            if sender_identity.identity_type == IdentityTypeEnum.EMAIL:
                raise InvalidConfigurationError(
                    f"Sender identity '{sender_identity.display_name}' is incomplete. "
                    f"Please add an email configuration before using it for reminders."
                )
            else:
                raise InvalidConfigurationError(
                    f"Sender identity '{sender_identity.display_name}' is incomplete. "
                    f"Please complete the setup before using it for reminders."
                )
        
        # Validate notification type is compatible with sender identity type
        if sender_identity.identity_type == IdentityTypeEnum.EMAIL and reminder_in.notification_type != NotificationType.EMAIL:
            raise InvalidConfigurationError("EMAIL sender identity can only be used with EMAIL notification type")
        
        if sender_identity.identity_type == IdentityTypeEnum.PHONE and reminder_in.notification_type not in [NotificationType.SMS, NotificationType.WHATSAPP]:
            raise InvalidConfigurationError("PHONE sender identity can only be used with SMS or WHATSAPP notification types")
        
        # Create reminder with user_id
        if isinstance(reminder_in, dict):
            obj_data = reminder_in.copy()
            obj_data["user_id"] = user_id
        else:
            obj_data = reminder_in.model_dump()
            obj_data["user_id"] = user_id
        
        # Create the reminder
        created_reminder = self.repository.create(db, obj_in=obj_data)
        
        # Add clients to the reminder if specified
        if hasattr(reminder_in, 'client_ids') and reminder_in.client_ids:
            from app.services.reminderRecipient import reminder_recipient_service
            for client_id in reminder_in.client_ids:
                reminder_recipient_service.create_reminder_recipient(
                    db,
                    obj_in={"reminder_id": created_reminder.id, "client_id": client_id},
                    user_id=user_id
                )
        
        return created_reminder
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update reminder")
    @with_event_emission(make_reminder_updated_event)
    def update_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int, 
        reminder_in: ReminderUpdate, 
        user_id: int
    ) -> Reminder:
        """
        Update an existing reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            reminder_in: Reminder update schema
            user_id: User ID for authorization
            
        Returns:
            Reminder: Updated reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
            InvalidConfigurationError: If reminder configuration is invalid
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # Validate updated reminder configuration
        if getattr(reminder_in, 'is_recurring', reminder.is_recurring) and not getattr(reminder_in, 'recurrence_pattern', reminder.recurrence_pattern):
            raise InvalidConfigurationError("Recurring reminders must have a recurrence pattern")
        
        # Check notification type compatibility if sender_identity_id or notification_type is being updated
        from app.services.senderIdentity import sender_identity_service
        from app.models.senderIdentities import IdentityTypeEnum
        
        # If sender_identity_id is being updated, check against the notification_type
        if hasattr(reminder_in, 'sender_identity_id') and reminder_in.sender_identity_id:
            sender_identity = sender_identity_service.get_sender_identity(
                db,
                sender_identity_id=reminder_in.sender_identity_id,
                user_id=user_id
            )
            
            # Use the new notification_type if provided, otherwise use the existing one
            notification_type = reminder_in.notification_type if hasattr(reminder_in, 'notification_type') and reminder_in.notification_type else reminder.notification_type
            
            if sender_identity.identity_type == IdentityTypeEnum.EMAIL and notification_type != NotificationType.EMAIL:
                raise InvalidConfigurationError("EMAIL sender identity can only be used with EMAIL notification type")
            
            if sender_identity.identity_type == IdentityTypeEnum.PHONE and notification_type not in [NotificationType.SMS, NotificationType.WHATSAPP]:
                raise InvalidConfigurationError("PHONE sender identity can only be used with SMS or WHATSAPP notification types")
        
        # If notification_type is being updated, check against the sender_identity_id
        elif hasattr(reminder_in, 'notification_type') and reminder_in.notification_type:
            # Use the existing sender_identity_id
            sender_identity = sender_identity_service.get_sender_identity(
                db,
                sender_identity_id=reminder.sender_identity_id,
                user_id=user_id
            )
            
            if sender_identity.identity_type == IdentityTypeEnum.EMAIL and reminder_in.notification_type != NotificationType.EMAIL:
                raise InvalidConfigurationError("EMAIL sender identity can only be used with EMAIL notification type")
            
            if sender_identity.identity_type == IdentityTypeEnum.PHONE and reminder_in.notification_type not in [NotificationType.SMS, NotificationType.WHATSAPP]:
                raise InvalidConfigurationError("PHONE sender identity can only be used with SMS or WHATSAPP notification types")
        
        # Update the reminder
        updated_reminder = self.repository.update(db, db_obj=reminder, obj_in=reminder_in)
        
        return updated_reminder
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete reminder")
    @with_event_emission(make_reminder_deleted_event)
    def delete_reminder(self, db: Session, *, reminder_id: int, user_id: int) -> Reminder:
        """
        Delete a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID for authorization
            
        Returns:
            Reminder: Deleted reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # Delete the reminder
        deleted_reminder = self.repository.delete(db, id=reminder_id)
        
        return deleted_reminder
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark reminder as active/inactive")
    @with_event_emission(make_reminder_updated_event)
    def set_reminder_active_status(
        self, 
        db: Session, 
        *, 
        reminder_id: int, 
        user_id: int, 
        is_active: bool
    ) -> Reminder:
        """
        Mark a reminder as active or inactive.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID for authorization
            is_active: Whether the reminder should be active
            
        Returns:
            Reminder: Updated reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # Update the reminder's active status
        updated_reminder = self.repository.update(db, db_obj=reminder, obj_in={"is_active": is_active})
        
        return updated_reminder

# Create singleton instance
reminder_service = ReminderService() 