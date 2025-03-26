from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

from app.core.repositories.base import BaseRepository
from app.models.reminders import Reminder, ReminderTypeEnum, NotificationTypeEnum
from app.schemas.reminders import ReminderCreate, ReminderUpdate

class ReminderRepository(BaseRepository[Reminder, ReminderCreate, ReminderUpdate]):
    """
    Repository for Reminder model with additional reminder-specific operations.
    """
    
    def __init__(self):
        super().__init__(Reminder)
    
    def get_by_user_id(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Reminder]:
        """
        Get all reminders for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        query = db.query(Reminder).filter(Reminder.user_id == user_id)
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.offset(skip).limit(limit).all()
    
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
        query = db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.reminder_date >= datetime.utcnow()
            )
        )
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.order_by(Reminder.reminder_date).limit(limit).all()
    
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
        query = db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.is_recurring == True
            )
        )
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.all()
    
    def get_reminders_by_type(
        self, 
        db: Session, 
        *, 
        user_id: int,
        reminder_type: ReminderTypeEnum,
        active_only: bool = True
    ) -> List[Reminder]:
        """
        Get reminders by type for a user.
        
        Args:
            db: Database session
            user_id: User ID
            reminder_type: Type of reminder
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        query = db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.reminder_type == reminder_type
            )
        )
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.all()
    
    def get_reminders_by_notification_type(
        self, 
        db: Session, 
        *, 
        user_id: int,
        notification_type: NotificationTypeEnum,
        active_only: bool = True
    ) -> List[Reminder]:
        """
        Get reminders by notification type for a user.
        
        Args:
            db: Database session
            user_id: User ID
            notification_type: Type of notification
            active_only: Whether to return only active reminders
            
        Returns:
            List[Reminder]: List of reminders
        """
        query = db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.notification_type == notification_type
            )
        )
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.all()
    
    def get_reminder_with_stats(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: int
    ) -> Optional[Reminder]:
        """
        Get a reminder with its statistics.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: User ID
            
        Returns:
            Optional[Reminder]: Reminder with stats if found, None otherwise
        """
        return (
            db.query(Reminder)
            .filter(Reminder.id == reminder_id, Reminder.user_id == user_id)
            .first()
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
        query = db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.reminder_date >= start_date,
                Reminder.reminder_date <= end_date
            )
        )
        
        if active_only:
            query = query.filter(Reminder.is_active == True)
            
        return query.order_by(Reminder.reminder_date).all()

# Create singleton instance
reminder_repository = ReminderRepository() 