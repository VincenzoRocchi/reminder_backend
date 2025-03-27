from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.client import client_repository
from app.schemas.clients import ClientCreate, ClientUpdate, Client, ClientDetail
from app.core.exceptions import ClientNotFoundError, ClientAlreadyExistsError

class ClientService:
    """
    Service layer for Client operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = client_repository
    
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
        return self.repository.get_by_phone_number(
            db, 
            phone_number=phone_number, 
            user_id=user_id
        )
    
    def get_user_clients(
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
    
    def create_client(self, db: Session, *, client_in: ClientCreate, user_id: int) -> Client:
        """
        Create a new client.
        
        Args:
            db: Database session
            client_in: Client creation data
            user_id: User ID
            
        Returns:
            Client: Created client
            
        Raises:
            ClientAlreadyExistsError: If client with same email/phone exists
        """
        # Check for existing client with same email
        if client_in.email:
            existing_client = self.get_client_by_email(db, email=client_in.email, user_id=user_id)
            if existing_client:
                raise ClientAlreadyExistsError(
                    f"Client with email {client_in.email} already exists"
                )
        
        # Check for existing client with same phone number
        if client_in.phone_number:
            existing_client = self.get_client_by_phone_number(
                db, 
                phone_number=client_in.phone_number, 
                user_id=user_id
            )
            if existing_client:
                raise ClientAlreadyExistsError(
                    f"Client with phone number {client_in.phone_number} already exists"
                )
        
        # Create client with user_id
        obj_in_data = client_in.model_dump()
        db_obj = self.repository.model(**obj_in_data)
        db_obj.user_id = user_id
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_client(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: int,
        client_in: ClientUpdate | Dict[str, Any]
    ) -> Client:
        """
        Update a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID
            client_in: Update data
            
        Returns:
            Client: Updated client
            
        Raises:
            ClientNotFoundError: If client not found
            ClientAlreadyExistsError: If new email/phone conflicts with existing client
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        
        # If email is being updated, check for conflicts
        if isinstance(client_in, dict):
            email = client_in.get("email")
        else:
            email = client_in.email
            
        if email and email != client.email:
            existing_client = self.get_client_by_email(db, email=email, user_id=user_id)
            if existing_client:
                raise ClientAlreadyExistsError(
                    f"Client with email {email} already exists"
                )
        
        # If phone number is being updated, check for conflicts
        if isinstance(client_in, dict):
            phone_number = client_in.get("phone_number")
        else:
            phone_number = client_in.phone_number
            
        if phone_number and phone_number != client.phone_number:
            existing_client = self.get_client_by_phone_number(
                db, 
                phone_number=phone_number, 
                user_id=user_id
            )
            if existing_client:
                raise ClientAlreadyExistsError(
                    f"Client with phone number {phone_number} already exists"
                )
        
        return self.repository.update(db, db_obj=client, obj_in=client_in)
    
    def delete_client(self, db: Session, *, client_id: int, user_id: int) -> Client:
        """
        Delete a client.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID
            
        Returns:
            Client: Deleted client
            
        Raises:
            ClientNotFoundError: If client not found
        """
        client = self.get_client(db, client_id=client_id, user_id=user_id)
        return self.repository.delete(db, id=client_id)
    
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