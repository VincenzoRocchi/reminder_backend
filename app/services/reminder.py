from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.schemas.reminders import (
    ReminderCreate, 
    ReminderUpdate, 
    Reminder, 
    ReminderDetail,
    ReminderType,
    NotificationType
)
from app.core.exceptions import (
    ReminderNotFoundError,
    ClientNotFoundError,
    InvalidConfigurationError
)

class ReminderService:
    """
    Service layer for Reminder operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = reminder_repository
        self.client_repository = client_repository
    
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
    
    def get_user_reminders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Reminder]:
        """
        Get all reminders for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        return self.repository.get_by_user_id(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
    
    def get_upcoming_reminders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Reminder]:
        """
        Get upcoming reminders for a user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of records to return
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of upcoming reminders
        """
        return self.repository.get_upcoming_reminders(
            db,
            user_id=user_id,
            limit=limit,
            active_only=active_only
        )
    
    def get_recurring_reminders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        active_only: bool = True
    ) -> List[Reminder]:
        """
        Get recurring reminders for a user.
        
        Args:
            db: Database session
            user_id: User ID
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of recurring reminders
        """
        return self.repository.get_recurring_reminders(
            db,
            user_id=user_id,
            active_only=active_only
        )
    
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
            reminder_in: Reminder creation data
            user_id: User ID
            
        Returns:
            Reminder: Created reminder
            
        Raises:
            ClientNotFoundError: If any client not found
            InvalidConfigurationError: If email/sender configuration is missing
        """
        # Validate clients exist
        for client_id in reminder_in.client_ids:
            client = self.client_repository.get(db, id=client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Validate email configuration if needed
        if reminder_in.notification_type == NotificationType.EMAIL:
            if not reminder_in.email_configuration_id:
                raise InvalidConfigurationError(
                    "Email configuration is required for email notifications"
                )
        
        # Validate sender identity if needed
        if reminder_in.notification_type in [NotificationType.SMS, NotificationType.WHATSAPP]:
            if not reminder_in.sender_identity_id:
                raise InvalidConfigurationError(
                    "Sender identity is required for SMS/WhatsApp notifications"
                )
        
        # Create reminder with user_id
        reminder_data = reminder_in.model_dump()
        reminder_data["user_id"] = user_id
        return self.repository.create(db, obj_in=ReminderCreate(**reminder_data))
    
    def update_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: int,
        reminder_in: ReminderUpdate | Dict[str, Any]
    ) -> Reminder:
        """
        Update a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            reminder_in: Update data
            
        Returns:
            Reminder: Updated reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If any client not found
            InvalidConfigurationError: If email/sender configuration is missing
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # If clients are being updated, validate them
        if isinstance(reminder_in, dict):
            client_ids = reminder_in.get("client_ids")
        else:
            client_ids = reminder_in.client_ids
            
        if client_ids:
            for client_id in client_ids:
                client = self.client_repository.get(db, id=client_id)
                if not client or client.user_id != user_id:
                    raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        # Validate email configuration if needed
        if isinstance(reminder_in, dict):
            notification_type = reminder_in.get("notification_type")
            email_config_id = reminder_in.get("email_configuration_id")
            sender_id = reminder_in.get("sender_identity_id")
        else:
            notification_type = reminder_in.notification_type
            email_config_id = reminder_in.email_configuration_id
            sender_id = reminder_in.sender_identity_id
            
        if notification_type == NotificationType.EMAIL and not email_config_id:
            raise InvalidConfigurationError(
                "Email configuration is required for email notifications"
            )
            
        if notification_type in [NotificationType.SMS, NotificationType.WHATSAPP] and not sender_id:
            raise InvalidConfigurationError(
                "Sender identity is required for SMS/WhatsApp notifications"
            )
        
        return self.repository.update(db, db_obj=reminder, obj_in=reminder_in)
    
    def delete_reminder(self, db: Session, *, reminder_id: int, user_id: int) -> Reminder:
        """
        Delete a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            
        Returns:
            Reminder: Deleted reminder
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        return self.repository.delete(db, id=reminder_id)
    
    def get_reminder_with_stats(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: int
    ) -> ReminderDetail:
        """
        Get a reminder with its statistics.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            
        Returns:
            ReminderDetail: Reminder with statistics
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        reminder = self.get_reminder(db, reminder_id=reminder_id, user_id=user_id)
        
        # Get statistics
        client_ids = [r.client_id for r in reminder.reminder_recipients]
        notifications_count = len(reminder.notifications)
        sent_count = len([n for n in reminder.notifications if n.status == "SENT"])
        failed_count = len([n for n in reminder.notifications if n.status == "FAILED"])
        
        # Create ReminderDetail object
        reminder_data = Reminder.model_validate(reminder).model_dump()
        return ReminderDetail(
            **reminder_data,
            clients=client_ids,
            notifications_count=notifications_count,
            sent_count=sent_count,
            failed_count=failed_count
        )
    
    def get_reminders_by_date_range(
        self, 
        db: Session, 
        *, 
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        active_only: bool = True
    ) -> List[Reminder]:
        """
        Get reminders within a date range for a user.
        
        Args:
            db: Database session
            user_id: User ID
            start_date: Start date
            end_date: End date
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        return self.repository.get_reminders_by_date_range(
            db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            active_only=active_only
        )

# Create singleton instance
reminder_service = ReminderService() 