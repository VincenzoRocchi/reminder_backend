from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.repositories.reminderRecipient import reminder_recipient_repository
from app.repositories.reminder import reminder_repository
from app.repositories.client import client_repository
from app.models.reminderRecipient import ReminderRecipient
from app.schemas.reminderRecipient import ReminderRecipientCreate, ReminderRecipientUpdate
from app.core.exceptions import ReminderNotFoundError, ClientNotFoundError, InvalidOperationError
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.dispatcher import event_dispatcher
from app.events.definitions.client_events import (
    create_client_added_to_reminder_event,
    create_client_removed_from_reminder_event
)
from app.events.utils import emit_event_safely, with_event_emission

# Event factory functions for decorators
def make_client_added_event(service, db, obj_in, user_id, result):
    """
    Create a client added to reminder event.
    
    Args:
        service: The service instance
        db: Database session
        obj_in: Reminder recipient creation schema
        user_id: User ID for authorization
        result: Created reminder recipient (function result)
        
    Returns:
        Event for client added to reminder
    """
    # Get client and reminder for the event
    client = client_repository.get(db, id=result.client_id)
    reminder = reminder_repository.get(db, id=result.reminder_id)
    
    return create_client_added_to_reminder_event(
        client_id=client.id,
        reminder_id=reminder.id,
        user_id=reminder.user_id,
        client_name=client.name,
        reminder_title=reminder.title
    )

def make_client_removed_event(service, db, reminder_recipient_id, user_id, result):
    """
    Create a client removed from reminder event.
    
    Args:
        service: The service instance
        db: Database session
        reminder_recipient_id: ID of the recipient to delete
        user_id: User ID for authorization (optional)
        result: Deleted reminder recipient (function result)
        
    Returns:
        Event for client removed from reminder
    """
    # Client and reminder IDs are stored in the result
    client_id = result.client_id
    reminder_id = result.reminder_id
    
    # Get client and reminder for the event
    client = client_repository.get(db, id=client_id)
    reminder = reminder_repository.get(db, id=reminder_id)
    
    if client and reminder:
        return create_client_removed_from_reminder_event(
            client_id=client_id,
            reminder_id=reminder_id,
            user_id=reminder.user_id,
            client_name=client.name,
            reminder_title=reminder.title
        )
    return None

# Helper functions for bulk operations
def emit_client_added_events(db: Session, clients: List, reminder_id: int, user_id: int) -> None:
    """
    Emit events for multiple clients added to a reminder.
    
    Args:
        db: Database session
        clients: List of client objects or IDs
        reminder_id: Reminder ID
        user_id: User ID
    """
    reminder = reminder_repository.get(db, id=reminder_id)
    if not reminder:
        return
        
    for client in clients:
        client_id = client.id if hasattr(client, 'id') else client
        client_obj = client if hasattr(client, 'name') else client_repository.get(db, id=client_id)
        
        if client_obj:
            event = create_client_added_to_reminder_event(
                client_id=client_id,
                reminder_id=reminder_id,
                user_id=user_id,
                client_name=client_obj.name,
                reminder_title=reminder.title
            )
            emit_event_safely(event)

def emit_client_removed_events(db: Session, client_data: Dict, reminder_id: int, user_id: int) -> None:
    """
    Emit events for multiple clients removed from a reminder.
    
    Args:
        db: Database session
        client_data: Dictionary of client IDs to client objects
        reminder_id: Reminder ID
        user_id: User ID
    """
    reminder = reminder_repository.get(db, id=reminder_id)
    if not reminder:
        return
        
    for client_id, client in client_data.items():
        event = create_client_removed_from_reminder_event(
            client_id=client_id,
            reminder_id=reminder_id,
            user_id=user_id,
            client_name=client.name,
            reminder_title=reminder.title
        )
        emit_event_safely(event)

class ReminderRecipientService:
    """
    Service for ReminderRecipient operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = reminder_recipient_repository
    
    @handle_exceptions(error_message="Failed to get reminder recipient")
    def get_reminder_recipient(
        self, 
        db: Session, 
        *, 
        reminder_recipient_id: int
    ) -> ReminderRecipient:
        """
        Get a reminder recipient by ID.
        
        Args:
            db: Database session
            reminder_recipient_id: Reminder recipient ID
            
        Returns:
            ReminderRecipient: Reminder recipient
            
        Raises:
            InvalidOperationError: If reminder recipient not found
        """
        reminder_recipient = self.repository.get(db, id=reminder_recipient_id)
        if not reminder_recipient:
            raise InvalidOperationError(f"Reminder recipient with ID {reminder_recipient_id} not found")
        return reminder_recipient
    
    @handle_exceptions(error_message="Failed to get reminder recipients by reminder")
    def get_reminder_recipients_by_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderRecipient]:
        """
        Get all recipients for a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            user_id: Optional user ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        # Verify reminder exists
        reminder = reminder_repository.get(db, id=reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            
        # If user_id is provided, verify reminder belongs to user
        if user_id and reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            
        return self.repository.get_by_reminder_id(
            db, reminder_id=reminder_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get reminder recipients by client")
    def get_reminder_recipients_by_client(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReminderRecipient]:
        """
        Get all reminders for a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: Optional user ID for authorization
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ReminderRecipient]: List of reminder recipients
            
        Raises:
            ClientNotFoundError: If client not found
        """
        # Verify client exists
        client = client_repository.get(db, id=client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
            
        # If user_id is provided, verify client belongs to user
        if user_id and client.user_id != user_id:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
            
        return self.repository.get_by_client_id(
            db, client_id=client_id, skip=skip, limit=limit)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create reminder recipient")
    @with_event_emission(make_client_added_event)
    def create_reminder_recipient(
        self, 
        db: Session, 
        *, 
        obj_in: ReminderRecipientCreate, 
        user_id: Optional[int] = None
    ) -> ReminderRecipient:
        """
        Create a new reminder recipient.
        
        Args:
            db: Database session
            obj_in: Reminder recipient creation schema
            user_id: Optional user ID for authorization
            
        Returns:
            ReminderRecipient: Created reminder recipient
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If client not found
            InvalidOperationError: If reminder recipient already exists
        """
        # Verify reminder exists
        reminder = reminder_repository.get(db, id=obj_in.reminder_id)
        if not reminder:
            raise ReminderNotFoundError(f"Reminder with ID {obj_in.reminder_id} not found")
            
        # If user_id is provided, verify reminder belongs to user
        if user_id and reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {obj_in.reminder_id} not found")
            
        # Verify client exists
        client = client_repository.get(db, id=obj_in.client_id)
        if not client:
            raise ClientNotFoundError(f"Client with ID {obj_in.client_id} not found")
            
        # Verify reminder and client belong to the same user
        if reminder.user_id != client.user_id:
            raise InvalidOperationError("Reminder and client must belong to the same user")
            
        # Check if association already exists
        existing = self.repository.get_by_reminder_and_client(
            db, reminder_id=obj_in.reminder_id, client_id=obj_in.client_id)
        if existing:
            raise InvalidOperationError("This client is already associated with this reminder")
        
        # Create the reminder recipient
        created_recipient = self.repository.create(db, obj_in=obj_in)
        
        return created_recipient
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete reminder recipient")
    @with_event_emission(make_client_removed_event)
    def delete_reminder_recipient(
        self, 
        db: Session, 
        *, 
        reminder_recipient_id: int,
        user_id: Optional[int] = None
    ) -> ReminderRecipient:
        """
        Delete a reminder recipient.
        
        Args:
            db: Database session
            reminder_recipient_id: Reminder recipient ID
            user_id: Optional user ID for authorization
            
        Returns:
            ReminderRecipient: Deleted reminder recipient
            
        Raises:
            InvalidOperationError: If reminder recipient not found
        """
        reminder_recipient = self.get_reminder_recipient(db, reminder_recipient_id=reminder_recipient_id)
        
        # If user_id is provided, verify ownership
        if user_id:
            reminder = reminder_repository.get(db, id=reminder_recipient.reminder_id)
            if not reminder or reminder.user_id != user_id:
                raise InvalidOperationError(f"Reminder recipient with ID {reminder_recipient_id} not found")
        
        # Delete the reminder recipient
        deleted_recipient = self.repository.delete(db, id=reminder_recipient_id)
        
        return deleted_recipient
    
    @with_transaction
    @handle_exceptions(error_message="Failed to associate clients with reminder")
    def add_clients_to_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        client_ids: List[int],
        user_id: int
    ) -> List[ReminderRecipient]:
        """
        Add multiple clients to a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            client_ids: List of client IDs
            user_id: User ID for authorization
            
        Returns:
            List[ReminderRecipient]: List of created reminder recipients
            
        Raises:
            ReminderNotFoundError: If reminder not found
            ClientNotFoundError: If any client not found
            InvalidOperationError: If clients already associated
        """
        # Verify reminder exists and belongs to user
        reminder = reminder_repository.get(db, id=reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
            
        # Get existing associations
        existing_recipients = self.get_reminder_recipients_by_reminder(
            db, reminder_id=reminder_id, user_id=user_id)
        existing_client_ids = {r.client_id for r in existing_recipients}
        
        # Filter out clients that are already associated
        new_client_ids = [cid for cid in client_ids if cid not in existing_client_ids]
        
        # Create new associations
        created_recipients = []
        created_clients = []
        
        for client_id in new_client_ids:
            # Verify client exists and belongs to user
            client = client_repository.get(db, id=client_id)
            if not client or client.user_id != user_id:
                raise ClientNotFoundError(f"Client with ID {client_id} not found")
                
            # Create association
            recipient_data = ReminderRecipientCreate(
                reminder_id=reminder_id,
                client_id=client_id
            )
            created_recipient = self.repository.create(db, obj_in=recipient_data)
            created_recipients.append(created_recipient)
            created_clients.append(client)
        
        # Emit events for all added clients
        if created_clients:
            emit_client_added_events(db, created_clients, reminder_id, user_id)
            
        return created_recipients
    
    @with_transaction
    @handle_exceptions(error_message="Failed to remove clients from reminder")
    def remove_clients_from_reminder(
        self, 
        db: Session, 
        *, 
        reminder_id: int,
        client_ids: List[int],
        user_id: int
    ) -> int:
        """
        Remove multiple clients from a reminder.
        
        Args:
            db: Database session
            reminder_id: Reminder ID
            client_ids: List of client IDs
            user_id: User ID for authorization
            
        Returns:
            int: Number of removed associations
            
        Raises:
            ReminderNotFoundError: If reminder not found
        """
        # Verify reminder exists and belongs to user
        reminder = reminder_repository.get(db, id=reminder_id)
        if not reminder or reminder.user_id != user_id:
            raise ReminderNotFoundError(f"Reminder with ID {reminder_id} not found")
        
        # Fetch all client details before removal for events
        clients = {}
        for client_id in client_ids:
            client = client_repository.get(db, id=client_id)
            if client and client.user_id == user_id:
                clients[client_id] = client
        
        # Remove associations
        removed_count = self.repository.delete_by_reminder_and_clients(
            db, reminder_id=reminder_id, client_ids=client_ids)
        
        # Emit client removed from reminder events
        if clients:
            emit_client_removed_events(db, clients, reminder_id, user_id)
        
        return removed_count

# Create singleton instance
reminder_recipient_service = ReminderRecipientService() 