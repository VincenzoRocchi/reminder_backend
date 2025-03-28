from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.client import client_repository
from app.schemas.clients import ClientCreate, ClientUpdate, Client, ClientDetail
from app.core.exceptions import ClientNotFoundError, ClientAlreadyExistsError
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import emit_event_safely, with_event_emission
from app.events.definitions.client_events import (
    create_client_created_event,
    create_client_updated_event,
    create_client_deleted_event
)

# Event factory functions for decorators
def make_client_created_event(service, db, client_in, user_id, result):
    """
    Create a client created event.
    
    Args:
        service: The service instance
        db: Database session
        client_in: Client creation schema
        user_id: User ID
        result: Created client (function result)
        
    Returns:
        Event for client created
    """
    return create_client_created_event(
        client_id=result.id,
        user_id=result.user_id,
        name=result.name,
        email=result.email,
        phone_number=result.phone_number,
        is_active=result.is_active
    )

def make_client_updated_event(service, db, client_id, client_in, user_id, result):
    """
    Create a client updated event.
    
    Args:
        service: The service instance
        db: Database session
        client_id: Client ID
        client_in: Client update schema
        user_id: User ID
        result: Updated client (function result)
        
    Returns:
        Event for client updated
    """
    return create_client_updated_event(
        client_id=result.id,
        user_id=result.user_id,
        name=result.name,
        email=result.email,
        phone_number=result.phone_number,
        is_active=result.is_active
    )

def make_client_deleted_event(service, db, client_id, user_id, result):
    """
    Create a client deleted event.
    
    Args:
        service: The service instance
        db: Database session
        client_id: Client ID
        user_id: User ID
        result: Deleted client (function result)
        
    Returns:
        Event for client deleted
    """
    return create_client_deleted_event(
        client_id=client_id,
        user_id=user_id,
        name=result.name
    )

class ClientService:
    """
    Service layer for Client operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = client_repository
    
    @handle_exceptions(error_message="Failed to get client")
    def get_client(self, db: Session, *, client_id: int, user_id: int) -> Client:
        """
        Get a client by ID.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID
            
        Returns:
            Client: Client object
            
        Raises:
            ClientNotFoundError: If client not found
        """
        client = self.repository.get(db, id=client_id)
        if not client or client.user_id != user_id:
            raise ClientNotFoundError(f"Client with ID {client_id} not found")
        return client
    
    @handle_exceptions(error_message="Failed to get client by email")
    def get_client_by_email(
        self, 
        db: Session, 
        *, 
        email: str,
        user_id: Optional[int] = None
    ) -> Optional[Client]:
        """
        Get a client by email.
        
        Args:
            db: Database session
            email: Client's email
            user_id: Optional user ID to filter by
            
        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        return self.repository.get_by_email(db, email=email, user_id=user_id)
    
    @handle_exceptions(error_message="Failed to get client by phone number")
    def get_client_by_phone_number(
        self, 
        db: Session, 
        *, 
        phone_number: str,
        user_id: Optional[int] = None
    ) -> Optional[Client]:
        """
        Get a client by phone number.
        
        Args:
            db: Database session
            phone_number: Client's phone number
            user_id: Optional user ID to filter by
            
        Returns:
            Optional[Client]: Client if found, None otherwise
        """
        return self.repository.get_by_phone_number(db, phone_number=phone_number, user_id=user_id)
    
    @handle_exceptions(error_message="Failed to get clients by user ID")
    def get_clients_by_user_id(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        search: str = None
    ) -> List[Client]:
        """
        Get all clients for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active clients
            search: Optional search term to filter by name or email
            
        Returns:
            List[Client]: List of clients
        """
        return self.repository.get_by_user_id(
            db, 
            user_id=user_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
            search=search
        )
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create client")
    @with_event_emission(lambda service, db, client_in, user_id, result: make_client_created_event(service, db, client_in, user_id, result))
    def create_client(self, db: Session, *, client_in: ClientCreate, user_id: int) -> Client:
        """
        Create a new client.
        
        Args:
            db: Database session
            client_in: Client creation schema
            user_id: User ID to associate with the client
            
        Returns:
            Client: Created client
            
        Raises:
            ClientAlreadyExistsError: If client with same email exists
        """
        # Check if client with same email exists for this user
        if client_in.email:
            existing_client = self.repository.get_by_email(db, email=client_in.email, user_id=user_id)
            if existing_client:
                raise ClientAlreadyExistsError(f"Client with email {client_in.email} already exists")
        
        # Prepare data with user_id
        if isinstance(client_in, dict):
            obj_data = client_in.copy()
            obj_data["user_id"] = user_id
        else:
            obj_data = client_in.model_dump()
            obj_data["user_id"] = user_id
        
        # Create the client    
        created_client = self.repository.create(db, obj_in=obj_data)
        
        return created_client
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update client")
    @with_event_emission(lambda service, db, client_id, client_in, user_id, result: make_client_updated_event(service, db, client_id, client_in, user_id, result))
    def update_client(
        self, 
        db: Session, 
        *, 
        client_id: int, 
        client_in: ClientUpdate, 
        user_id: int
    ) -> Client:
        """
        Update an existing client.
        
        Args:
            db: Database session
            client_id: Client ID
            client_in: Client update schema
            user_id: User ID for authorization
            
        Returns:
            Client: Updated client
            
        Raises:
            ClientNotFoundError: If client not found
            ClientAlreadyExistsError: If updated email conflicts with existing client
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        
        # Check for email conflicts if email is being changed
        if hasattr(client_in, 'email') and client_in.email and client_in.email != client.email:
            existing_client = self.repository.get_by_email(db, email=client_in.email, user_id=user_id)
            if existing_client:
                raise ClientAlreadyExistsError(f"Client with email {client_in.email} already exists")
        
        # Update the client
        updated_client = self.repository.update(db, db_obj=client, obj_in=client_in)
        
        return updated_client
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete client")
    @with_event_emission(lambda service, db, client_id, user_id, result: make_client_deleted_event(service, db, client_id, user_id, result))
    def delete_client(self, db: Session, *, client_id: int, user_id: int) -> Client:
        """
        Delete a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID for authorization
            
        Returns:
            Client: Deleted client
            
        Raises:
            ClientNotFoundError: If client not found
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        
        # Delete the client
        deleted_client = self.repository.delete(db, id=client_id)
        
        return deleted_client
    
    @with_transaction
    @handle_exceptions(error_message="Failed to mark client as active/inactive")
    def set_client_active_status(
        self, 
        db: Session, 
        *, 
        client_id: int, 
        user_id: int, 
        is_active: bool
    ) -> Client:
        """
        Set a client's active status.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID for authorization
            is_active: New active status
            
        Returns:
            Client: Updated client
            
        Raises:
            ClientNotFoundError: If client not found
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        
        # Update the client's active status
        updated_client = self.repository.update(db, db_obj=client, obj_in={"is_active": is_active})
        
        return updated_client
    
    def get_active_clients(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Client]:
        """
        Get all active clients for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Client]: List of active clients
        """
        return self.repository.get_active_clients(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    
    def get_clients_by_contact_method(
        self, 
        db: Session, 
        *, 
        user_id: int,
        contact_method: str,
        active_only: bool = True
    ) -> List[Client]:
        """
        Get clients by preferred contact method.
        
        Args:
            db: Database session
            user_id: User ID
            contact_method: Preferred contact method
            active_only: Whether to return only active clients
            
        Returns:
            List[Client]: List of clients
        """
        return self.repository.get_clients_by_contact_method(
            db,
            user_id=user_id,
            contact_method=contact_method,
            active_only=active_only
        )
    
    def get_client_with_stats(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: int
    ) -> ClientDetail:
        """
        Get a client with their statistics.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID
            
        Returns:
            ClientDetail: Client with statistics
            
        Raises:
            ClientNotFoundError: If client not found
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        
        # Get statistics
        reminders_count = len(client.reminder_recipients)
        active_reminders_count = len([
            r for r in client.reminder_recipients 
            if r.reminder.is_active
        ])
        notifications_count = len(client.notifications)
        
        # Create ClientDetail object
        client_data = Client.model_validate(client).model_dump()
        return ClientDetail(
            **client_data,
            reminders_count=reminders_count,
            active_reminders_count=active_reminders_count,
            notifications_count=notifications_count
        )

# Create singleton instance
client_service = ClientService() 