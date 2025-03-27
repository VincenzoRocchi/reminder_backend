from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.emailConfiguration import email_configuration_repository
from app.repositories.user import user_repository
from app.schemas.emailConfigurations import EmailConfigurationCreate, EmailConfigurationUpdate, EmailConfiguration
from app.core.exceptions import UserNotFoundError, EmailConfigurationNotFoundError, EmailConfigurationAlreadyExistsError

class EmailConfigurationService:
    """
    Service for EmailConfiguration operations.
    Implements business logic and uses the repository for data access.
    """
    
    def get_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int
    ) -> Optional[EmailConfiguration]:
        """
        Get an email configuration by ID.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            
        Returns:
            Optional[EmailConfiguration]: Email configuration if found, None otherwise
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration is not found
        """
        email_configuration = email_configuration_repository.get(db, id=email_configuration_id)
        if not email_configuration:
            raise EmailConfigurationNotFoundError(f"Email configuration with ID {email_configuration_id} not found")
        return email_configuration
    
    def get_user_email_configurations(
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
            
        Raises:
            UserNotFoundError: If user is not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return email_configuration_repository.get_by_user_id(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
    
    def get_active_configurations(
        self, 
        db: Session, 
        *, 
        user_id: int
    ) -> List[EmailConfiguration]:
        """
        Get all active email configurations for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List[EmailConfiguration]: List of active email configurations
            
        Raises:
            UserNotFoundError: If user is not found
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        return email_configuration_repository.get_active_configurations(
            db,
            user_id=user_id
        )
    
    def create_email_configuration(
        self, 
        db: Session, 
        *, 
        user_id: int,
        obj_in: EmailConfigurationCreate
    ) -> EmailConfiguration:
        """
        Create a new email configuration.
        
        Args:
            db: Database session
            user_id: User ID
            obj_in: EmailConfigurationCreate object
            
        Returns:
            EmailConfiguration: Created email configuration
            
        Raises:
            UserNotFoundError: If user is not found
            EmailConfigurationAlreadyExistsError: If configuration with same name or email exists
        """
        # Verify user exists
        user = user_repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Check for existing configuration with same name
        existing_by_name = email_configuration_repository.get_by_name(
            db,
            user_id=user_id,
            configuration_name=obj_in.configuration_name
        )
        if existing_by_name:
            raise EmailConfigurationAlreadyExistsError(
                f"Email configuration with name '{obj_in.configuration_name}' already exists"
            )
        
        # Check for existing configuration with same email
        existing_by_email = email_configuration_repository.get_by_email(
            db,
            user_id=user_id,
            email_from=obj_in.email_from
        )
        if existing_by_email:
            raise EmailConfigurationAlreadyExistsError(
                f"Email configuration with email '{obj_in.email_from}' already exists"
            )
        
        # Create new configuration
        db_obj = EmailConfiguration(
            **obj_in.model_dump(),
            user_id=user_id
        )
        return email_configuration_repository.create(db, obj_in=db_obj)
    
    def update_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        obj_in: EmailConfigurationUpdate
    ) -> EmailConfiguration:
        """
        Update an email configuration.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            obj_in: EmailConfigurationUpdate object
            
        Returns:
            EmailConfiguration: Updated email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration is not found
            EmailConfigurationAlreadyExistsError: If new name or email conflicts with existing
        """
        # Verify email configuration exists
        email_configuration = self.get_email_configuration(db, email_configuration_id=email_configuration_id)
        
        # Check for name conflict if being updated
        if obj_in.configuration_name:
            existing_by_name = email_configuration_repository.get_by_name(
                db,
                user_id=email_configuration.user_id,
                configuration_name=obj_in.configuration_name
            )
            if existing_by_name and existing_by_name.id != email_configuration_id:
                raise EmailConfigurationAlreadyExistsError(
                    f"Email configuration with name '{obj_in.configuration_name}' already exists"
                )
        
        # Check for email conflict if being updated
        if obj_in.email_from:
            existing_by_email = email_configuration_repository.get_by_email(
                db,
                user_id=email_configuration.user_id,
                email_from=obj_in.email_from
            )
            if existing_by_email and existing_by_email.id != email_configuration_id:
                raise EmailConfigurationAlreadyExistsError(
                    f"Email configuration with email '{obj_in.email_from}' already exists"
                )
        
        return email_configuration_repository.update(
            db,
            db_obj=email_configuration,
            obj_in=obj_in
        )
    
    def delete_email_configuration(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int
    ) -> EmailConfiguration:
        """
        Delete an email configuration.
        
        Args:
            db: Database session
            email_configuration_id: Email configuration ID
            
        Returns:
            EmailConfiguration: Deleted email configuration
            
        Raises:
            EmailConfigurationNotFoundError: If email configuration is not found
        """
        # Verify email configuration exists
        email_configuration = self.get_email_configuration(db, email_configuration_id=email_configuration_id)
        return email_configuration_repository.remove(db, id=email_configuration_id)

# Create singleton instance
email_configuration_service = EmailConfigurationService() 