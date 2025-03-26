from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.repositories.base import BaseRepository
from app.models.reminderRecipient import ReminderRecipient
from app.schemas.reminderRecipient import ReminderRecipientCreate, ReminderRecipientUpdate

class ReminderRecipientRepository(BaseRepository[ReminderRecipient, ReminderRecipientCreate, ReminderRecipientUpdate]):
    """
    Repository for ReminderRecipient operations.
    Extends the base repository with reminder recipient-specific operations.
    """
    
    def get_by_reminder_id(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderRecipient]:
        """
        Get all recipients for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
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
    ) -> List[ReminderRecipient]:
        """
        Get all reminders for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
        """
        return db.query(self.model).filter(
            self.model.client_id == client_id
        ).offset(skip).limit(limit).all()
    
    def get_by_reminder_and_client(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        client_id: int
    ) -> Optional[ReminderRecipient]:
        """
        Get a reminder recipient by reminder and client IDs.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            client_id: Client ID
            
        Returns:
            Optional[ReminderRecipient]: Reminder recipient if found, None otherwise
        """
        return db.query(self.model).filter(
            and_(
                self.model.reminder_id == reminder_id,
                self.model.client_id == client_id
            )
        ).first()
    
    def get_client_reminders(
        self, 
        db: Session, 
        *, 
        client_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderRecipient]:
        """
        Get all reminders for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
        """
        return self.get_by_client_id(
            db,
            client_id=client_id,
            skip=skip,
            limit=limit
        )
    
    def get_reminder_recipients(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderRecipient]:
        """
        Get all recipients for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
        """
        return self.get_by_reminder_id(
            db,
            reminder_id=reminder_id,
            skip=skip,
            limit=limit
        )

# Create singleton instance
reminder_recipient_repository = ReminderRecipientRepository(ReminderRecipient) 