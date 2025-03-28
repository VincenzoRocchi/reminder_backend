from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime

from app.core.repositories.base import BaseRepository
from app.models.notifications import Notification, NotificationStatusEnum
from app.schemas.notifications import NotificationCreate, NotificationUpdate

class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """
    Repository for Notification operations.
    Extends the base repository with notification-specific operations.
    """
    
    def get_by_reminder_id(
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
        return db.query(self.model).filter(
            self.model.reminder_id == reminder_id
        ).offset(skip).limit(limit).all()
    
    def get_by_client_id(
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
        return db.query(self.model).filter(
            self.model.client_id == client_id
        ).offset(skip).limit(limit).all()
    
    def get_by_status(
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
        return db.query(self.model).filter(
            self.model.status == status
        ).offset(skip).limit(limit).all()
    
    def get_by_type(
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
        return db.query(self.model).filter(
            self.model.notification_type == notification_type
        ).offset(skip).limit(limit).all()
    
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
        return self.get_by_status(
            db,
            status=NotificationStatusEnum.PENDING,
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
        return self.get_by_status(
            db,
            status=NotificationStatusEnum.FAILED,
            skip=skip,
            limit=limit
        )
    
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
        """
        notification = self.get(db, id=notification_id)
        if notification:
            notification.status = NotificationStatusEnum.SENT
            notification.sent_at = datetime.utcnow()
            db.commit()
            db.refresh(notification)
        return notification
    
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
        """
        notification = self.get(db, id=notification_id)
        if notification:
            notification.status = NotificationStatusEnum.FAILED
            notification.error_message = error_message
            db.commit()
            db.refresh(notification)
        return notification
    
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
        """
        notification = self.get(db, id=notification_id)
        if notification:
            notification.status = NotificationStatusEnum.CANCELLED
            db.commit()
            db.refresh(notification)
        return notification

# Create singleton instance
notification_repository = NotificationRepository(Notification) 