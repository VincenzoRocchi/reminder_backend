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
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import queue_event
from app.events.definitions.sender_identity_events import (
    create_sender_identity_created_event,
    create_sender_identity_updated_event,
    create_sender_identity_deleted_event,
    create_sender_identity_verified_event,
    create_default_sender_identity_set_event
)

class SenderIdentityService:
    """
    Service layer for SenderIdentity operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = sender_identity_repository
    
    @handle_exceptions(error_message="Failed to get sender identity")
    def get_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: Optional[int] = None
    ) -> SenderIdentity:
        """
        Get a sender identity by ID.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: Optional user ID for authorization
            
        Returns:
            SenderIdentity: Sender identity
            
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
    
    @handle_exceptions(error_message="Failed to get sender identities by user")
    def get_sender_identities_by_user(
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
        return self.repository.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get sender identities by type")
    def get_sender_identities_by_type(
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
            identity_type: Type of identity (EMAIL, PHONE, etc.)
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[SenderIdentity]: List of sender identities
        """
        return self.repository.get_by_type(
            db, user_id=user_id, identity_type=identity_type, skip=skip, limit=limit)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create sender identity")
    def create_sender_identity(
        self, 
        db: Session, 
        *, 
        obj_in: SenderIdentityCreate, 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Create a new sender identity.
        
        Args:
            db: Database session
            obj_in: Sender identity creation schema
            user_id: User ID
            
        Returns:
            SenderIdentity: Created sender identity
            
        Raises:
            UserNotFoundError: If user not found
            SenderIdentityAlreadyExistsError: If identity with same value exists
            InvalidConfigurationError: If identity configuration is invalid
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
            
        # Validate identity type
        if obj_in.identity_type not in [e.value for e in IdentityTypeEnum]:
            raise InvalidConfigurationError(f"Invalid identity type: {obj_in.identity_type}")
            
        # Check if identity with same value and type exists
        existing_identity = self.repository.get_by_value(
            db, 
            user_id=user_id, 
            identity_type=obj_in.identity_type, 
            value=obj_in.value
        )
        if existing_identity:
            raise SenderIdentityAlreadyExistsError(
                f"Sender identity with value '{obj_in.value}' already exists")
        
        # Create identity with user_id
        obj_in_data = obj_in.model_dump()
        obj_in_data["user_id"] = user_id
        
        # Create the sender identity
        sender_identity = self.repository.create(db, obj_in=obj_in_data)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_sender_identity_created_event(
                identity_id=sender_identity.id,
                user_id=sender_identity.user_id,
                identity_type=sender_identity.identity_type,
                value=sender_identity.value,
                display_name=sender_identity.display_name or "",
                is_verified=sender_identity.is_verified,
                is_default=sender_identity.is_default
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return sender_identity
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update sender identity")
    def update_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        obj_in: SenderIdentityUpdate, 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Update an existing sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            obj_in: Sender identity update schema
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
            SenderIdentityAlreadyExistsError: If updated value conflicts with existing identity
            InvalidConfigurationError: If identity configuration is invalid
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # Validate identity type if being updated
        if hasattr(obj_in, 'identity_type') and obj_in.identity_type is not None:
            if obj_in.identity_type not in [e.value for e in IdentityTypeEnum]:
                raise InvalidConfigurationError(f"Invalid identity type: {obj_in.identity_type}")
        
        # Check for value conflicts if value is being updated
        if hasattr(obj_in, 'value') and obj_in.value is not None and obj_in.value != sender_identity.value:
            # Use the new type if it's being updated, otherwise use the existing type
            identity_type = getattr(obj_in, 'identity_type', sender_identity.identity_type)
            
            existing_identity = self.repository.get_by_value(
                db, 
                user_id=user_id, 
                identity_type=identity_type, 
                value=obj_in.value
            )
            if existing_identity and existing_identity.id != sender_identity_id:
                raise SenderIdentityAlreadyExistsError(
                    f"Sender identity with value '{obj_in.value}' already exists")
        
        # Update the sender identity 
        updated_identity = self.repository.update(db, db_obj=sender_identity, obj_in=obj_in)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_sender_identity_updated_event(
                identity_id=updated_identity.id,
                user_id=updated_identity.user_id,
                identity_type=updated_identity.identity_type,
                value=updated_identity.value,
                display_name=updated_identity.display_name,
                is_verified=updated_identity.is_verified,
                is_default=updated_identity.is_default
            )
            queue_event(kwargs['_transaction_id'], event)
                
        return updated_identity
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete sender identity")
    def delete_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Delete a sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Deleted sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # Store identity information before deletion for event emission
        identity_id = sender_identity.id
        identity_user_id = sender_identity.user_id
        identity_type = sender_identity.identity_type
        identity_value = sender_identity.value
        identity_display_name = sender_identity.display_name
        
        # Delete the sender identity
        deleted_identity = self.repository.delete(db, id=sender_identity_id)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_sender_identity_deleted_event(
                identity_id=identity_id,
                user_id=identity_user_id,
                identity_type=identity_type,
                value=identity_value,
                display_name=identity_display_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return deleted_identity
    
    @handle_exceptions(error_message="Failed to get default sender identity")
    def get_default_sender_identity(
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
            identity_type: Type of identity (EMAIL, PHONE, etc.)
            
        Returns:
            Optional[SenderIdentity]: Default sender identity if found, None otherwise
        """
        return self.repository.get_default_identity(db, user_id=user_id, identity_type=identity_type)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to set default sender identity")
    def set_default_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Set a sender identity as the default for its type.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
        """
        # Verify configuration exists and belongs to user
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # Set as default
        updated_identity = self.repository.set_default_identity(db, identity_id=sender_identity_id, user_id=user_id)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_default_sender_identity_set_event(
                identity_id=updated_identity.id,
                user_id=updated_identity.user_id,
                identity_type=updated_identity.identity_type,
                value=updated_identity.value,
                display_name=updated_identity.display_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return updated_identity
    
    @with_transaction
    @handle_exceptions(error_message="Failed to verify sender identity")
    def verify_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        user_id: int,
        verification_code: str,
        **kwargs
    ) -> SenderIdentity:
        """
        Verify a sender identity using a verification code.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID for authorization
            verification_code: Verification code to validate
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
            InvalidOperationError: If verification fails
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # In a real implementation, this would verify the code against a stored value
        # For now, we'll just set it as verified directly
        
        # Set identity as verified
        updated_identity = self.repository.update(
            db, db_obj=sender_identity, obj_in={"is_verified": True})
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_sender_identity_verified_event(
                identity_id=updated_identity.id,
                user_id=updated_identity.user_id,
                identity_type=updated_identity.identity_type,
                value=updated_identity.value,
                display_name=updated_identity.display_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return updated_identity

# Create singleton instance
sender_identity_service = SenderIdentityService() 