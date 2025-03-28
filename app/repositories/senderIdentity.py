from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.repositories.base import BaseRepository
from app.models.senderIdentities import SenderIdentity, IdentityTypeEnum
from app.schemas.senderIdentities import SenderIdentityCreate, SenderIdentityUpdate

class SenderIdentityRepository(BaseRepository[SenderIdentity, SenderIdentityCreate, SenderIdentityUpdate]):
    """
    Repository for SenderIdentity operations.
    Extends the base repository with sender identity-specific operations.
    """
    
    def get_by_user_id(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SenderIdentity]:
        """
        Get all sender identities for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[SenderIdentity]: List of sender identities
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_by_filter(
        self, 
        db: Session, 
        **kwargs
    ) -> Optional[SenderIdentity]:
        """
        Get sender identity by filter criteria.
        
        Args:
            db: Database session
            **kwargs: Filter criteria (user_id, identity_type, email, phone_number, etc.)
            
        Returns:
            Optional[SenderIdentity]: Sender identity if found, None otherwise
        """
        query = db.query(self.model)
        
        for key, value in kwargs.items():
            if hasattr(self.model, key) and value is not None:
                query = query.filter(getattr(self.model, key) == value)
                
        return query.first()
    
    def get_default_identity(
        self, 
        db: Session, 
        *, 
        user_id: int,
        identity_type: IdentityTypeEnum
    ) -> Optional[SenderIdentity]:
        """
        Get the default sender identity of a specific type for a user.
        
        Args:
            db: Database session
            user_id: User ID
            identity_type: Type of sender identity
            
        Returns:
            Optional[SenderIdentity]: Default sender identity if found, None otherwise
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.identity_type == identity_type,
                self.model.is_default == True,
                self.model.is_verified == True
            )
        ).first()

# Create singleton instance
sender_identity_repository = SenderIdentityRepository(SenderIdentity) 