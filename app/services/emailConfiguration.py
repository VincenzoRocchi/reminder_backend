from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.emailConfiguration import email_configuration_repository
from app.repositories.user import user_repository
from app.schemas.emailConfigurations import EmailConfigurationCreate, EmailConfigurationUpdate, EmailConfiguration
from app.core.exceptions import UserNotFoundError, EmailConfigurationNotFoundError, EmailConfigurationAlreadyExistsError
from app.core.error_handling import handle_exceptions, with_transaction

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
        user_id: int
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
        
        return email_configuration_repository.create(db, obj_in=obj_in_data)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update email configuration")
    def update_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        obj_in: EmailConfigurationUpdate,
        user_id: int
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
        
        return email_configuration_repository.update(db, db_obj=email_configuration, obj_in=obj_in)
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete email configuration")
    def delete_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        user_id: int
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
        return email_configuration_repository.delete(db, id=email_configuration_id)
    
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
        user_id: int
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
        # Clear current default
        current_default = self.get_default_email_configuration(db, user_id=user_id)
        if current_default:
            email_configuration_repository.update(
                db, db_obj=current_default, obj_in={"is_default": False})
        
        # Set new default
        email_configuration = self.get_email_configuration_by_user(
            db, user_id=user_id, email_configuration_id=email_configuration_id)
        return email_configuration_repository.update(
            db, db_obj=email_configuration, obj_in={"is_default": True})

# Create singleton instance
email_configuration_service = EmailConfigurationService() 