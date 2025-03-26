from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
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
    
    def get_by_type(
        self, 
        db: Session, 
        *, 
        user_id: int,
        identity_type: IdentityTypeEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[SenderIdentity]:
        """
        Get all sender identities of a specific type for a user.
        
        Args:
            db: Database session
            user_id: User ID
            identity_type: Type of sender identity
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[SenderIdentity]: List of sender identities
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.identity_type == identity_type
            )
        ).offset(skip).limit(limit).all()
    
    def get_verified_identities(
        self, 
        db: Session, 
        *, 
        user_id: int
    ) -> List[SenderIdentity]:
        """
        Get all verified sender identities for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List[SenderIdentity]: List of verified sender identities
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.is_verified == True
            )
        ).all()
    
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
    
    def get_by_value(
        self, 
        db: Session, 
        *, 
        user_id: int,
        value: str
    ) -> Optional[SenderIdentity]:
        """
        Get a sender identity by value for a user.
        
        Args:
            db: Database session
            user_id: User ID
            value: Identity value (phone number or email)
            
        Returns:
            Optional[SenderIdentity]: Sender identity if found, None otherwise
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.value == value
            )
        ).first()

# Create singleton instance
sender_identity_repository = SenderIdentityRepository(SenderIdentity) 