from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.repositories.base import BaseRepository
from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientUpdate

class ClientRepository(BaseRepository[Client, ClientCreate, ClientUpdate]):
    """
    Repository for Client model with additional client-specific operations.
    """
    
    def __init__(self):
        super().__init__(Client)
    
    def get_by_user_id(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False
    ) -> List[Client]:
        """
        Get all clients for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to return only active clients
            
        Returns:
            List[Client]: List of clients
        """
        query = db.query(Client).filter(Client.user_id == user_id)
        
        if active_only:
            query = query.filter(Client.is_active == True)
            
        return query.offset(skip).limit(limit).all()
    
    def get_by_email(
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
        query = db.query(Client).filter(Client.email == email)
        
        if user_id:
            query = query.filter(Client.user_id == user_id)
            
        return query.first()
    
    def get_by_phone_number(
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
        query = db.query(Client).filter(
            or_(
                Client.phone_number == phone_number,
                Client.secondary_phone_number == phone_number,
                Client.whatsapp_phone_number == phone_number
            )
        )
        
        if user_id:
            query = query.filter(Client.user_id == user_id)
            
        return query.first()
    
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
        return self.get_by_user_id(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            active_only=True
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
        query = db.query(Client).filter(Client.user_id == user_id)
        
        if active_only:
            query = query.filter(Client.is_active == True)
            
        if contact_method == "EMAIL":
            query = query.filter(Client.email.isnot(None))
        elif contact_method == "SMS":
            query = query.filter(Client.phone_number.isnot(None))
        elif contact_method == "WHATSAPP":
            query = query.filter(Client.whatsapp_phone_number.isnot(None))
            
        return query.all()
    
    def get_client_with_stats(
        self, 
        db: Session, 
        *, 
        client_id: int,
        user_id: int
    ) -> Optional[Client]:
        """
        Get a client with their statistics.
        
        Args:
            db: Database session
            client_id: Client ID
            user_id: User ID
            
        Returns:
            Optional[Client]: Client with stats if found, None otherwise
        """
        return (
            db.query(Client)
            .filter(Client.id == client_id, Client.user_id == user_id)
            .first()
        )

# Create singleton instance
client_repository = ClientRepository() 