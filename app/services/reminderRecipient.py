from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.reminderRecipient import reminder_recipient_repository
from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.schemas.reminderRecipient import ReminderRecipientCreate, ReminderRecipientUpdate, ReminderRecipient
from app.core.exceptions import ReminderNotFoundError, ClientNotFoundError, ReminderRecipientNotFoundError

class ReminderRecipientService:
    """
    Service for ReminderRecipient operations.
    Implements business logic and uses the repository for data access.
    """
    
    def get_reminder_recipient(
        self, 
        db: Session, 
        *, 
        reminder_recipient_id: int
    ) -> Optional[ReminderRecipient]:
        """
        Get a reminder recipient by ID.
        
        Args:
            db: Database session
            reminder_recipient_id: Reminder recipient ID
            
        Returns:
            Optional[ReminderRecipient]: Reminder recipient if found, None otherwise
            
        Raises:
            ReminderRecipientNotFoundError: If reminder recipient is not found
        """
        reminder_recipient = reminder_recipient_repository.get(db, id=reminder_recipient_id)
        if not reminder_recipient:
            raise ReminderRecipientNotFoundError(f"Reminder recipient with ID {reminder_recipient_id} not found")
        return reminder_recipient
    
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
            
        Raises:
            ReminderNotFoundError: If reminder is not found
        """
        # Verify reminder exists
        reminder = reminder_repository.get(db, id=reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
        
        return reminder_recipient_repository.get_reminder_recipients(
            db,
            reminder_id=reminder_id,
            skip=skip,
            limit=limit
        )
    
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
            
        Raises:
            ClientNotFoundError: If client is not found
        """
        # Verify client exists
        client = client_repository.get(db, id=client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        
        return reminder_recipient_repository.get_client_reminders(
            db,
            client_id=client_id,
            skip=skip,
            limit=limit
        )
    
    def create_reminder_recipient(
        self, 
        db: Session, 
        *, 
        obj_in: ReminderRecipientCreate
    ) -> ReminderRecipient:
        """
        Create a new reminder recipient.
        
        Args:
            db: Database session
            obj_in: ReminderRecipientCreate object
            
        Returns:
            ReminderRecipient: Created reminder recipient
            
        Raises:
            ReminderNotFoundError: If reminder is not found
            ClientNotFoundError: If client is not found
        """
        # Verify reminder exists
        reminder = reminder_repository.get(db, id=obj_in.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {obj_in.reminder_id} not found")
        
        # Verify client exists
        client = client_repository.get(db, id=obj_in.client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {obj_in.client_id} not found")
        
        return reminder_recipient_repository.create(db, obj_in=obj_in)
    
    def update_reminder_recipient(
        self, 
        db: Session, 
        *, 
        reminder_recipient_id: int,
        obj_in: ReminderRecipientUpdate
    ) -> ReminderRecipient:
        """
        Update a reminder recipient.
        
        Args:
            db: Database session
            reminder_recipient_id: Reminder recipient ID
            obj_in: ReminderRecipientUpdate object
            
        Returns:
            ReminderRecipient: Updated reminder recipient
            
        Raises:
            ReminderRecipientNotFoundError: If reminder recipient is not found
            ReminderNotFoundError: If new reminder is not found
            ClientNotFoundError: If new client is not found
        """
        # Verify reminder recipient exists
        reminder_recipient = self.get_reminder_recipient(db, reminder_recipient_id=reminder_recipient_id)
        
        # Verify new reminder exists if being updated
        if obj_in.reminder_id:
            reminder = reminder_repository.get(db, id=obj_in.reminder_id)
            if not reminder:
                raise ReminderNotFoundError(f"Reminder with ID {obj_in.reminder_id} not found")
        
        # Verify new client exists if being updated
        if obj_in.client_id:
            client = client_repository.get(db, id=obj_in.client_id)
            if not client:
                raise ClientNotFoundError(f"Client with ID {obj_in.client_id} not found")
        
        return reminder_recipient_repository.update(
            db,
            db_obj=reminder_recipient,
            obj_in=obj_in
        )
    
    def delete_reminder_recipient(
        self, 
        db: Session, 
        *, 
        reminder_recipient_id: int
    ) -> ReminderRecipient:
        """
        Delete a reminder recipient.
        
        Args:
            db: Database session
            reminder_recipient_id: Reminder recipient ID
            
        Returns:
            ReminderRecipient: Deleted reminder recipient
            
        Raises:
            ReminderRecipientNotFoundError: If reminder recipient is not found
        """
        # Verify reminder recipient exists
        reminder_recipient = self.get_reminder_recipient(db, reminder_recipient_id=reminder_recipient_id)
        return reminder_recipient_repository.remove(db, id=reminder_recipient_id)

# Create singleton instance
reminder_recipient_service = ReminderRecipientService() 