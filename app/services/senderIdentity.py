from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.senderIdentity import sender_identity_repository
from app.repositories.user import user_repository
from app.models.senderIdentities import IdentityTypeEnum
from app.schemas.senderIdentities import (
    SenderIdentityCreate, 
    SenderIdentityUpdate, 
    SenderIdentity
)
from app.core.exceptions import (
    SenderIdentityNotFoundError,
    SenderIdentityAlreadyExistsError,
    InvalidConfigurationError,
    UserNotFoundError
)

class SenderIdentityService:
    """
    Service layer for SenderIdentity operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = sender_identity_repository
    
    def get_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: Optional[int] = None
    ) -> Optional[SenderIdentity]:
        """
        Get a sender identity by ID.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: Optional user ID for authorization
            
        Returns:
            Optional[SenderIdentity]: Sender identity if found, None otherwise
            
        Raises:
            SenderIdentityNotFoundError: If sender identity is not found
        """
        sender_identity = self.repository.get(db, id=sender_identity_id)
        if not sender_identity:
            raise SenderIdentityNotFoundError(f"Sender identity with ID {sender_identity_id} not found")
        
        # Check if identity belongs to user if user_id is provided
        if user_id and sender_identity.user_id != user_id:
            raise SenderIdentityNotFoundError(f"Sender identity with ID {sender_identity_id} not found")
            
        return sender_identity
    
    def get_user_sender_identities(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        identity_type: Optional[IdentityTypeEnum] = None
    ) -> List[SenderIdentity]:
        """
        Get all sender identities for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            identity_type: Optional filter by identity type
            
        Returns:
            List[SenderIdentity]: List of sender identities
            
        Raises:
            UserNotFoundError: If user is not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # If identity type is specified, filter by type
        if identity_type:
            return self.get_identities_by_type(
                db,
                user_id=user_id,
                identity_type=identity_type,
                skip=skip,
                limit=limit
            )
        
        return self.repository.get_by_user_id(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    
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
            
        Raises:
            UserNotFoundError: If user is not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return self.repository.get_verified_identities(
            db,
            user_id=user_id
        )
    
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
            
        Raises:
            UserNotFoundError: If user is not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return self.repository.get_default_identity(
            db,
            user_id=user_id,
            identity_type=identity_type
        )
    
    def get_identities_by_type(
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
            identity_type: Type of identity (PHONE or EMAIL)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[SenderIdentity]: List of sender identities
        """
        return self.repository.get_by_type(
            db,
            user_id=user_id,
            identity_type=identity_type,
            skip=skip,
            limit=limit
        )
    
    def get_identity_by_value(
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
        return self.repository.get_by_value(
            db,
            user_id=user_id,
            value=value
        )
    
    def create_sender_identity(
        self, 
        db: Session, 
        *, 
        user_id: int,
        obj_in: SenderIdentityCreate
    ) -> SenderIdentity:
        """
        Create a new sender identity.
        
        Args:
            db: Database session
            user_id: User ID
            obj_in: SenderIdentityCreate object
            
        Returns:
            SenderIdentity: Created sender identity
            
        Raises:
            UserNotFoundError: If user is not found
            SenderIdentityAlreadyExistsError: If identity with same value exists
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Check for existing identity with same value
        existing_identity = self.get_identity_by_value(
            db,
            user_id=user_id,
            value=obj_in.value
        )
        if existing_identity:
            raise SenderIdentityAlreadyExistsError(
                f"Sender identity with value '{obj_in.value}' already exists"
            )
        
        # If this is the first identity of its type, make it default
        identities_of_type = self.get_identities_by_type(
            db,
            user_id=user_id,
            identity_type=obj_in.identity_type
        )
        if not identities_of_type:
            obj_in_dict = obj_in.model_dump()
            obj_in_dict["is_default"] = True
            obj_in_dict["user_id"] = user_id
            db_obj = self.repository.model(**obj_in_dict)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        
        # Create new identity
        obj_in_dict = obj_in.model_dump()
        obj_in_dict["user_id"] = user_id
        db_obj = self.repository.model(**obj_in_dict)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        obj_in: SenderIdentityUpdate,
        user_id: Optional[int] = None
    ) -> SenderIdentity:
        """
        Update a sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            obj_in: SenderIdentityUpdate object
            user_id: Optional user ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity is not found
            SenderIdentityAlreadyExistsError: If new value conflicts with existing
        """
        # Verify sender identity exists
        sender_identity = self.get_sender_identity(
            db, 
            sender_identity_id=sender_identity_id,
            user_id=user_id
        )
        
        # Check for value conflict if being updated
        if obj_in.value:
            existing_identity = self.get_identity_by_value(
                db,
                user_id=sender_identity.user_id,
                value=obj_in.value
            )
            if existing_identity and existing_identity.id != sender_identity_id:
                raise SenderIdentityAlreadyExistsError(
                    f"Sender identity with value '{obj_in.value}' already exists"
                )
        
        return self.repository.update(
            db,
            db_obj=sender_identity,
            obj_in=obj_in
        )
    
    def delete_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: Optional[int] = None
    ) -> SenderIdentity:
        """
        Delete a sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: Optional user ID for authorization
            
        Returns:
            SenderIdentity: Deleted sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity is not found
        """
        # Verify sender identity exists
        sender_identity = self.get_sender_identity(
            db, 
            sender_identity_id=sender_identity_id,
            user_id=user_id
        )
        return self.repository.delete(db, id=sender_identity_id)
    
    def verify_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: Optional[int] = None
    ) -> SenderIdentity:
        """
        Set a sender identity as verified.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: Optional user ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If identity not found
        """
        # In a real-world application, this would include verification logic
        
        # Get the identity, which also checks user_id if provided
        identity = self.get_sender_identity(
            db, 
            sender_identity_id=sender_identity_id,
            user_id=user_id
        )
        
        # Update the identity to set is_verified to True
        update_data = {"is_verified": True}
        return self.repository.update(
            db,
            db_obj=identity,
            obj_in=update_data
        )
    
    def set_default_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: int
    ) -> SenderIdentity:
        """
        Set a sender identity as default for a user.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If identity not found
        """
        identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        return self.repository.set_default_identity(db, identity_id=sender_identity_id, user_id=user_id)

# Create singleton instance
sender_identity_service = SenderIdentityService() 