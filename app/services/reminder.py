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
        if reminder_in.client_id:
            client = self.client_repository.get(db, id=reminder_in.client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {reminder_in.client_id} not found")
        
        # Validate reminder configuration
        if reminder_in.is_recurring and not reminder_in.recurrence_pattern:
            raise InvalidConfigurationError("Recurring reminders must have a recurrence pattern")
        
        # Create reminder with user_id
        if isinstance(reminder_in, dict):
            obj_data = reminder_in.copy()
            obj_data["user_id"] = user_id
        else:
            obj_data = reminder_in.model_dump()
            obj_data["user_id"] = user_id
            
        return self.repository.create(db, obj_in=obj_data)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update reminder")
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
            ClientNotFoundError: If client not found
            InvalidConfigurationError: If reminder configuration is invalid
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # If client_id is being changed, validate client exists and belongs to user
        if hasattr(reminder_in, 'client_id') and reminder_in.client_id and reminder_in.client_id != reminder.client_id:
            client = self.client_repository.get(db, id=reminder_in.client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {reminder_in.client_id} not found")
        
        # Validate recurrence pattern if set to recurring
        if hasattr(reminder_in, 'is_recurring') and reminder_in.is_recurring:
            # If reminder is being set to recurring, ensure it has a recurrence pattern
            if not reminder.recurrence_pattern and not getattr(reminder_in, 'recurrence_pattern', None):
                raise InvalidConfigurationError("Recurring reminders must have a recurrence pattern")
                
        return self.repository.update(db, db_obj=reminder, obj_in=reminder_in)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete reminder")
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
        return self.repository.delete(db, id=reminder_id)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark reminder as active/inactive")
    def set_reminder_active_status(
        self, 
        db: Session, 
        *, 
        reminder_id: int, 
        user_id: int, 
        is_active: bool
    ) -> Reminder:
        """
        Set a reminder's active status.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID for authorization
            is_active: New active status
            
        Returns:
            Reminder: Updated reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        return self.repository.update(db, db_obj=reminder, obj_in={"is_active": is_active})

# Create singleton instance
reminder_service = ReminderService() 