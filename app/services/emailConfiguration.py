from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.emailConfiguration import email_configuration_repository
from app.repositories.user import user_repository
from app.schemas.emailConfigurations import EmailConfigurationCreate, EmailConfigurationUpdate, EmailConfiguration
from app.core.exceptions import UserNotFoundError, EmailConfigurationNotFoundError, EmailConfigurationAlreadyExistsError
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import queue_event
from app.events.definitions.email_configuration_events import (
    create_email_configuration_created_event,
    create_email_configuration_updated_event,
    create_email_configuration_deleted_event,
    create_email_configuration_set_default_event
)

class EmailConfigurationService:
    """
    Service for EmailConfiguration operations.
    Implements business logic and uses the repository for data access.
    """
    
    @handle_exceptions(error_message="Failed to get email configuration")
    def get_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int
    ) -> EmailConfiguration:
        """
        Get an email configuration by ID.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            
        Returns:
            EmailConfiguration: Email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration is not found
        """
        email_configuration = email_configuration_repository.get(db, id=email_configuration_id)
        if not email_configuration:
            raise EmailConfigurationNotFoundError(f"Email configuration with ID {email_configuration_id} not found")
        return email_configuration
    
    @handle_exceptions(error_message="Failed to get email configuration by user")
    def get_email_configuration_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int,
        email_configuration_id: int
    ) -> EmailConfiguration:
        """
        Get an email configuration by ID and verify it belongs to the user.
        
        Args:
            db: Database session
            user_id: User ID
            email_configuration_id: Email configuration ID
            
        Returns:
            EmailConfiguration: Email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration is not found or doesn't belong to the user
        """
        email_configuration = self.get_email_configuration(db, email_configuration_id=email_configuration_id)
        if email_configuration.user_id != user_id:
            raise EmailConfigurationNotFoundError(f"Email configuration with ID {email_configuration_id} not found")
        return email_configuration
    
    @handle_exceptions(error_message="Failed to get email configurations by user")
    def get_email_configurations_by_user(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[EmailConfiguration]:
        """
        Get all email configurations for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[EmailConfiguration]: List of email configurations
        """
        return email_configuration_repository.get_by_user_id(db, user_id=user_id, skip=skip, limit=limit)
    
    @handle_exceptions(error_message="Failed to get email configuration by name")
    def get_email_configuration_by_name(
        self, 
        db: Session, 
        *, 
        user_id: int,
        configuration_name: str
    ) -> Optional[EmailConfiguration]:
        """
        Get an email configuration by name.
        
        Args:
            db: Database session
            user_id: User ID
            configuration_name: Configuration name
            
        Returns:
            Optional[EmailConfiguration]: Email configuration if found, None otherwise
        """
        return email_configuration_repository.get_by_name(
            db, user_id=user_id, configuration_name=configuration_name)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create email configuration")
    def create_email_configuration(
        self, 
        db: Session, 
        *, 
        obj_in: EmailConfigurationCreate, 
        user_id: int,
        **kwargs
    ) -> EmailConfiguration:
        """
        Create a new email configuration.
        
        Args:
            db: Database session
            obj_in: Email configuration creation schema
            user_id: User ID
            
        Returns:
            EmailConfiguration: Created email configuration
            
        Raises:
            UserNotFoundError: If user not found
            EmailConfigurationAlreadyExistsError: If configuration with same name exists
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
            
        # Check if configuration with same name exists
        existing_config = self.get_email_configuration_by_name(
            db, user_id=user_id, configuration_name=obj_in.configuration_name)
        if existing_config:
            raise EmailConfigurationAlreadyExistsError(
                f"Email configuration with name '{obj_in.configuration_name}' already exists")
        
        # Create configuration with user_id
        obj_in_data = obj_in.model_dump()
        obj_in_data["user_id"] = user_id
        
        created_config = email_configuration_repository.create(db, obj_in=obj_in_data)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_email_configuration_created_event(
                email_configuration_id=created_config.id,
                user_id=user_id,
                configuration_name=created_config.configuration_name,
                smtp_server=created_config.smtp_server,
                smtp_port=created_config.smtp_port,
                sender_email=created_config.sender_email,
                is_default=created_config.is_default
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return created_config
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update email configuration")
    def update_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        obj_in: EmailConfigurationUpdate,
        user_id: int,
        **kwargs
    ) -> EmailConfiguration:
        """
        Update an email configuration.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            obj_in: Email configuration update schema
            user_id: User ID for authorization
            
        Returns:
            EmailConfiguration: Updated email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration not found
            EmailConfigurationAlreadyExistsError: If new name conflicts with existing configuration
        """
        email_configuration = self.get_email_configuration_by_user(
            db, user_id=user_id, email_configuration_id=email_configuration_id)
        
        # If name is being updated, check for conflicts
        if hasattr(obj_in, 'configuration_name') and obj_in.configuration_name is not None:
            existing_config = self.get_email_configuration_by_name(
                db, user_id=user_id, configuration_name=obj_in.configuration_name)
            if existing_config and existing_config.id != email_configuration_id:
                raise EmailConfigurationAlreadyExistsError(
                    f"Email configuration with name '{obj_in.configuration_name}' already exists")
        
        updated_config = email_configuration_repository.update(db, db_obj=email_configuration, obj_in=obj_in)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            # Extract updated values from obj_in
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
                
            event = create_email_configuration_updated_event(
                email_configuration_id=updated_config.id,
                user_id=user_id,
                configuration_name=updated_config.configuration_name,
                smtp_server=updated_config.smtp_server if 'smtp_server' in update_data else None,
                smtp_port=updated_config.smtp_port if 'smtp_port' in update_data else None,
                sender_email=updated_config.sender_email if 'sender_email' in update_data else None,
                is_default=updated_config.is_default if 'is_default' in update_data else None
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return updated_config
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete email configuration")
    def delete_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        user_id: int,
        **kwargs
    ) -> EmailConfiguration:
        """
        Delete an email configuration.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            user_id: User ID for authorization
            
        Returns:
            EmailConfiguration: Deleted email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration not found
        """
        email_configuration = self.get_email_configuration_by_user(
            db, user_id=user_id, email_configuration_id=email_configuration_id)
        
        # Store configuration information before deletion for event emission
        config_id = email_configuration.id
        config_name = email_configuration.configuration_name
        
        deleted_config = email_configuration_repository.delete(db, id=email_configuration_id)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_email_configuration_deleted_event(
                email_configuration_id=config_id,
                user_id=user_id,
                configuration_name=config_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return deleted_config
    
    @handle_exceptions(error_message="Failed to get default email configuration")
    def get_default_email_configuration(
        self, 
        db: Session, 
        *, 
        user_id: int
    ) -> Optional[EmailConfiguration]:
        """
        Get the default email configuration for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Optional[EmailConfiguration]: Default email configuration if found, None otherwise
        """
        return email_configuration_repository.get_default(db, user_id=user_id)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to set default email configuration")
    def set_default_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        user_id: int,
        **kwargs
    ) -> EmailConfiguration:
        """
        Set an email configuration as default.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            user_id: User ID for authorization
            
        Returns:
            EmailConfiguration: Updated email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration not found
        """
        # Verify configuration exists and belongs to user
        email_configuration = self.get_email_configuration_by_user(
            db, user_id=user_id, email_configuration_id=email_configuration_id)
        
        # Set as default
        updated_config = email_configuration_repository.set_default(db, email_configuration_id=email_configuration_id, user_id=user_id)
        
        # Queue event for emission after transaction commits
        if '_transaction_id' in kwargs:
            event = create_email_configuration_set_default_event(
                email_configuration_id=updated_config.id,
                user_id=user_id,
                configuration_name=updated_config.configuration_name
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return updated_config

# Singleton instance
email_configuration_service = EmailConfigurationService() 