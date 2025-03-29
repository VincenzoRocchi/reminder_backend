from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session

from app.repositories.senderIdentity import sender_identity_repository
from app.repositories.user import user_repository
from app.repositories.emailConfiguration import email_configuration_repository
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
    UserNotFoundError,
    EmailConfigurationNotFoundError
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
    Service for managing sender identities.
    
    This service handles operations related to sender identities, including:
    - Creating new sender identities
    - Updating existing sender identities
    - Deleting sender identities
    - Verifying sender identities
    - Setting default sender identities
    """
    
    def get_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int,
        user_id: int
    ) -> SenderIdentity:
        """
        Get a sender identity by ID.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Sender identity schema object
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
        """
        sender_identity = sender_identity_repository.get(
            db, id=sender_identity_id
        )
        
        if not sender_identity:
            raise SenderIdentityNotFoundError(f"Sender identity not found with ID: {sender_identity_id}")
            
        if sender_identity.user_id != user_id:
            raise SenderIdentityNotFoundError(f"Sender identity not found with ID: {sender_identity_id}")
            
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
            identity_type: Filter by identity type
            
        Returns:
            List[SenderIdentity]: List of sender identities
        """
        return sender_identity_repository.get_by_user_id(
            db, user_id=user_id, skip=skip, limit=limit, identity_type=identity_type
        )
    
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
            identity_type: Type of sender identity
            
        Returns:
            Optional[SenderIdentity]: Default sender identity if found, None otherwise
        """
        return sender_identity_repository.get_default_identity(
            db, user_id=user_id, identity_type=identity_type
        )
    
    def get_by_email_or_phone(
        self, 
        db: Session, 
        *, 
        user_id: int,
        identity_type: IdentityTypeEnum,
        email: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Optional[SenderIdentity]:
        """
        Get a sender identity by email or phone number and type for a user.
        
        Args:
            db: Database session
            user_id: User ID
            identity_type: Type of identity
            email: Email address (for EMAIL type)
            phone_number: Phone number (for PHONE type)
            
        Returns:
            Optional[SenderIdentity]: Sender identity if found, None otherwise
        """
        if identity_type == IdentityTypeEnum.EMAIL and email:
            return sender_identity_repository.get_by_filter(
                db, user_id=user_id, identity_type=identity_type, email=email
            )
        elif identity_type == IdentityTypeEnum.PHONE and phone_number:
            return sender_identity_repository.get_by_filter(
                db, user_id=user_id, identity_type=identity_type, phone_number=phone_number
            )
        return None
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create sender identity")
    def create_sender_identity(
        self, 
        db: Session, 
        *, 
        obj_in: Union[SenderIdentityCreate, Dict[str, Any]], 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Create a new sender identity.
        
        Args:
            db: Database session
            obj_in: Sender identity create schema or dictionary
            user_id: User ID for ownership
            
        Returns:
            SenderIdentity: Created sender identity
            
        Raises:
            SenderIdentityAlreadyExistsError: If sender identity already exists
            InvalidConfigurationError: If identity configuration is invalid
            UserNotFoundError: If user not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User not found with ID: {user_id}")
        
        # Handle both dictionary and Pydantic model inputs
        if isinstance(obj_in, dict):
            identity_type = obj_in.get("identity_type")
            email = obj_in.get("email")
            phone_number = obj_in.get("phone_number")
            email_configuration_id = obj_in.get("email_configuration_id")
            is_default = obj_in.get("is_default", False)
            identity_dict = obj_in.copy()
        else:
            identity_type = obj_in.identity_type
            email = obj_in.email
            phone_number = obj_in.phone_number
            email_configuration_id = obj_in.email_configuration_id
            is_default = obj_in.is_default
            identity_dict = obj_in.model_dump(exclude_unset=True)
            
        # Check for configuration and validation errors
        if identity_type == IdentityTypeEnum.EMAIL:
            # Validate email configuration exists if specified
            if email_configuration_id:
                email_config = email_configuration_repository.get(
                    db, id=email_configuration_id
                )
                if not email_config or email_config.user_id != user_id:
                    raise EmailConfigurationNotFoundError(
                        f"Email configuration not found with ID: {email_configuration_id}"
                    )
            
            # Check if this email identity already exists
            existing = self.get_by_email_or_phone(
                db, 
                user_id=user_id, 
                identity_type=identity_type,
                email=email
            )
            
            if existing:
                raise SenderIdentityAlreadyExistsError(
                    f"Email sender identity already exists with email: {email}"
                )
        else:
            # Check if this phone number identity already exists
            existing = self.get_by_email_or_phone(
                db, 
                user_id=user_id, 
                identity_type=identity_type,
                phone_number=phone_number
            )
            
            if existing:
                raise SenderIdentityAlreadyExistsError(
                    f"Phone sender identity already exists with number: {phone_number}"
                )
        
        # If this is set to default, unset any existing default identities
        # of the same type
        if is_default:
            self._unset_existing_defaults(db, user_id=user_id, identity_type=identity_type)
        
        # Add user ID and verification status
        identity_dict["user_id"] = user_id
        identity_dict["is_verified"] = False  # New identities start unverified
        
        sender_identity = sender_identity_repository.create(db, obj_in=identity_dict)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            # Get the value based on identity type
            value = sender_identity.email if sender_identity.identity_type == IdentityTypeEnum.EMAIL else sender_identity.phone_number
            
            event = create_sender_identity_created_event(
                identity_id=sender_identity.id,
                user_id=sender_identity.user_id,
                identity_type=sender_identity.identity_type,
                value=value,
                display_name=sender_identity.display_name or "",
                is_verified=sender_identity.is_verified,
                is_default=sender_identity.is_default,
                email_configuration_id=sender_identity.email_configuration_id
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
        obj_in: Union[SenderIdentityUpdate, Dict[str, Any]], 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Update an existing sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            obj_in: Sender identity update schema or dictionary
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
            SenderIdentityAlreadyExistsError: If updated value conflicts with existing identity
            InvalidConfigurationError: If identity configuration is invalid
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # Handle both dictionary and Pydantic model inputs
        if isinstance(obj_in, dict):
            identity_type = obj_in.get("identity_type") or sender_identity.identity_type
            email = obj_in.get("email")
            phone_number = obj_in.get("phone_number")
            email_configuration_id = obj_in.get("email_configuration_id")
            is_default = obj_in.get("is_default")
            identity_dict = obj_in.copy()
        else:
            identity_type = obj_in.identity_type or sender_identity.identity_type
            email = obj_in.email if hasattr(obj_in, 'email') else None
            phone_number = obj_in.phone_number if hasattr(obj_in, 'phone_number') else None
            email_configuration_id = obj_in.email_configuration_id if hasattr(obj_in, 'email_configuration_id') else None
            is_default = obj_in.is_default if hasattr(obj_in, 'is_default') else None
            identity_dict = obj_in.model_dump(exclude_unset=True)
        
        # Check for configuration and validation errors
        if identity_type == IdentityTypeEnum.EMAIL:
            # Validate email configuration exists if specified
            if email_configuration_id:
                email_config = email_configuration_repository.get(
                    db, id=email_configuration_id
                )
                if not email_config or email_config.user_id != user_id:
                    raise EmailConfigurationNotFoundError(
                        f"Email configuration not found with ID: {email_configuration_id}"
                    )
            
            # Check if this email identity already exists (if changing email)
            if email and email != sender_identity.email:
                existing = self.get_by_email_or_phone(
                    db, 
                    user_id=user_id, 
                    identity_type=identity_type,
                    email=email
                )
                
                if existing and existing.id != sender_identity_id:
                    raise SenderIdentityAlreadyExistsError(
                        f"Email sender identity already exists with email: {email}"
                    )
        else:
            # Check if this phone number identity already exists (if changing phone)
            if phone_number and phone_number != sender_identity.phone_number:
                existing = self.get_by_email_or_phone(
                    db, 
                    user_id=user_id, 
                    identity_type=identity_type,
                    phone_number=phone_number
                )
                
                if existing and existing.id != sender_identity_id:
                    raise SenderIdentityAlreadyExistsError(
                        f"Phone sender identity already exists with number: {phone_number}"
                    )
        
        # If this is set to default, unset any existing default identities
        # of the same type
        if is_default:
            self._unset_existing_defaults(db, user_id=user_id, identity_type=identity_type)
        
        # If identity type is changing, we need to reset verification
        if "identity_type" in identity_dict and identity_dict["identity_type"] != sender_identity.identity_type:
            identity_dict["is_verified"] = False
        
        # Special handling for changes that might require re-verification
        if identity_type == IdentityTypeEnum.EMAIL and email and email != sender_identity.email:
            identity_dict["is_verified"] = False
        elif identity_type == IdentityTypeEnum.PHONE and phone_number and phone_number != sender_identity.phone_number:
            identity_dict["is_verified"] = False
        
        sender_identity = sender_identity_repository.update(
            db, db_obj=sender_identity, obj_in=identity_dict
        )
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            # Get the value based on identity type
            value = sender_identity.email if sender_identity.identity_type == IdentityTypeEnum.EMAIL else sender_identity.phone_number
            
            event = create_sender_identity_updated_event(
                identity_id=sender_identity.id,
                user_id=sender_identity.user_id,
                identity_type=sender_identity.identity_type,
                value=value,
                display_name=sender_identity.display_name or "",
                is_verified=sender_identity.is_verified,
                is_default=sender_identity.is_default,
                email_configuration_id=sender_identity.email_configuration_id
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return sender_identity
    
    def _unset_existing_defaults(
        self, 
        db: Session, 
        *, 
        user_id: int,
        identity_type: IdentityTypeEnum
    ) -> None:
        """
        Unset any existing default identities of the specified type.
        
        Args:
            db: Database session
            user_id: User ID
            identity_type: Type of identity
        """
        existing_default = self.get_default_sender_identity(
            db, user_id=user_id, identity_type=identity_type
        )
        
        if existing_default:
            sender_identity_repository.update(
                db, db_obj=existing_default, obj_in={"is_default": False}
            )
    
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
        
        # Get a copy of data for event emission
        identity_id = sender_identity.id
        identity_user_id = sender_identity.user_id
        identity_type = sender_identity.identity_type
        
        # Get the value based on identity type
        value = sender_identity.email if sender_identity.identity_type == IdentityTypeEnum.EMAIL else sender_identity.phone_number
        
        identity_name = sender_identity.display_name or ""
        
        # Delete the identity
        sender_identity = sender_identity_repository.delete(db, id=sender_identity_id)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_sender_identity_deleted_event(
                identity_id=identity_id,
                user_id=identity_user_id,
                identity_type=identity_type,
                value=value,
                display_name=identity_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return sender_identity
    
    @with_transaction
    @handle_exceptions(error_message="Failed to set verify status")
    def set_verification_status(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        is_verified: bool,
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Set verification status for a sender identity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            is_verified: Whether the identity is verified
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        # Update verification status
        sender_identity = sender_identity_repository.update(
            db, db_obj=sender_identity, obj_in={"is_verified": is_verified}
        )
        
        # Queue event for emission after transaction commits
        if is_verified and '_transaction_id' in kwargs:
            # Get the value based on identity type
            value = sender_identity.email if sender_identity.identity_type == IdentityTypeEnum.EMAIL else sender_identity.phone_number
            
            event = create_sender_identity_verified_event(
                identity_id=sender_identity.id,
                user_id=sender_identity.user_id,
                identity_type=sender_identity.identity_type,
                value=value,
                display_name=sender_identity.display_name or ""
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return sender_identity
    
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
            InvalidConfigurationError: If identity is not verified
        """
        sender_identity = self.get_sender_identity(db, sender_identity_id=sender_identity_id, user_id=user_id)
        
        if not sender_identity.is_verified:
            raise InvalidConfigurationError("Cannot set unverified identity as default")
        
        # Unset any existing defaults of the same type
        self._unset_existing_defaults(db, user_id=user_id, identity_type=sender_identity.identity_type)
        
        # Set this identity as default
        sender_identity = sender_identity_repository.update(
            db, db_obj=sender_identity, obj_in={"is_default": True}
        )
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            # Get the value based on identity type
            value = sender_identity.email if sender_identity.identity_type == IdentityTypeEnum.EMAIL else sender_identity.phone_number
            
            event = create_default_sender_identity_set_event(
                identity_id=sender_identity.id,
                user_id=sender_identity.user_id,
                identity_type=sender_identity.identity_type,
                value=value,
                display_name=sender_identity.display_name or ""
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return sender_identity

    @handle_exceptions(error_message="Failed to verify sender identity")
    def verify_sender_identity(
        self, 
        db: Session, 
        *, 
        sender_identity_id: int, 
        user_id: int,
        **kwargs
    ) -> SenderIdentity:
        """
        Verify a sender identity.
        
        In a real implementation, this would verify that the user actually 
        owns the phone number or email. This method serves as a wrapper 
        around set_verification_status for semantic clarity.
        
        Args:
            db: Database session
            sender_identity_id: Sender identity ID
            user_id: User ID for authorization
            
        Returns:
            SenderIdentity: Updated sender identity
            
        Raises:
            SenderIdentityNotFoundError: If sender identity not found
        """
        # In a real application, verification logic would go here
        # For now, we just set the verification status to true
        return self.set_verification_status(
            db,
            sender_identity_id=sender_identity_id,
            is_verified=True,
            user_id=user_id,
            **kwargs
        )

sender_identity_service = SenderIdentityService() 