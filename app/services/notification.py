from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.repositories.notification import notification_repository
from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.models.notifications import NotificationStatusEnum
from app.schemas.notifications import (
    NotificationCreate, 
    NotificationUpdate, 
    Notification,
    NotificationDetail
)
from app.core.exceptions import (
    NotificationNotFoundError,
    ReminderNotFoundError,
    ClientNotFoundError
)

class NotificationService:
    """
    Service layer for Notification operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = notification_repository
        self.reminder_repository = reminder_repository
        self.client_repository = client_repository
    
    def get_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Get a notification by ID.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Notification object
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.repository.get(db, id=notification_id)
        if not notification:
            raise NotificationNotFoundError(
                f"Notification with ID {notification_id} not found"
            )
        return notification
    
    def get_notification_detail(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> NotificationDetail:
        """
        Get a notification with extra details.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            NotificationDetail: Notification with extra details
            
        Raises:
            NotificationNotFoundError: If notification not found
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        
        # Get reminder details
        reminder = self.reminder_repository.get(db, id=notification.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(
                f"Reminder with ID {notification.reminder_id} not found"
            )
            
        # Get client details
        client = self.client_repository.get(db, id=notification.client_id)
        if not client:
            raise ClientNotFoundError(
                f"Client with ID {notification.client_id} not found"
            )
        
        # Create NotificationDetail object
        notification_data = Notification.model_validate(notification).model_dump()
        return NotificationDetail(
            **notification_data,
            reminder_title=reminder.title,
            client_name=client.name
        )
    
    def get_reminder_notifications(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_reminder_id(
            db,
            reminder_id=reminder_id,
            skip=skip,
            limit=limit
        )
    
    def get_client_notifications(
        self, 
        db: Session, 
        *, 
        client_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_client_id(
            db,
            client_id=client_id,
            skip=skip,
            limit=limit
        )
    
    def get_notifications_by_status(
        self, 
        db: Session, 
        *, 
        status: NotificationStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications with a specific status.
        
        Args:
            db: Database session
            status: Notification status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_status(
            db,
            status=status,
            skip=skip,
            limit=limit
        )
    
    def get_notifications_by_type(
        self, 
        db: Session, 
        *, 
        notification_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications of a specific type.
        
        Args:
            db: Database session
            notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of notifications
        """
        return self.repository.get_by_type(
            db,
            notification_type=notification_type,
            skip=skip,
            limit=limit
        )
    
    def get_pending_notifications(
        self, 
        db: Session, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all pending notifications.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of pending notifications
        """
        return self.repository.get_pending_notifications(
            db,
            skip=skip,
            limit=limit
        )
    
    def get_failed_notifications(
        self, 
        db: Session, 
        *, 
        skip: int = 0,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get all failed notifications.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Notification]: List of failed notifications
        """
        return self.repository.get_failed_notifications(
            db,
            skip=skip,
            limit=limit
        )
    
    def create_notification(
        self, 
        db: Session, 
        *, 
        notification_in: NotificationCreate
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            db: Database session
            notification_in: Notification creation data
            
        Returns:
            Notification: Created notification
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
        """
        # Validate reminder exists
        reminder = self.reminder_repository.get(db, id=notification_in.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(
                f"Reminder with ID {notification_in.reminder_id} not found"
            )
            
        # Validate client exists
        client = self.client_repository.get(db, id=notification_in.client_id)
        if not client:
            raise ClientNotFoundError(
                f"Client with ID {notification_in.client_id} not found"
            )
        
        return self.repository.create(db, obj_in=notification_in)
    
    def update_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        notification_in: NotificationUpdate | Dict[str, Any]
    ) -> Notification:
        """
        Update a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            notification_in: Update data
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.update(db, db_obj=notification, obj_in=notification_in)
    
    def delete_notification(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Delete a notification.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Deleted notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.delete(db, id=notification_id)
    
    def mark_as_sent(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Mark a notification as sent.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_sent(db, notification_id=notification_id)
    
    def mark_as_failed(
        self, 
        db: Session, 
        *, 
        notification_id: int,
        error_message: str
    ) -> Notification:
        """
        Mark a notification as failed.
        
        Args:
            db: Database session
            notification_id: Notification ID
            error_message: Error message
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_failed(
            db,
            notification_id=notification_id,
            error_message=error_message
        )
    
    def mark_as_cancelled(
        self, 
        db: Session, 
        *, 
        notification_id: int
    ) -> Notification:
        """
        Mark a notification as cancelled.
        
        Args:
            db: Database session
            notification_id: Notification ID
            
        Returns:
            Notification: Updated notification
            
        Raises:
            NotificationNotFoundError: If notification not found
        """
        notification = self.get_notification(db, notification_id=notification_id)
        return self.repository.mark_as_cancelled(db, notification_id=notification_id)

# Create singleton instance
notification_service = NotificationService() 