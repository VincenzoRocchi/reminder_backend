from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.repositories.base import BaseRepository
from app.models.emailConfigurations import EmailConfiguration
from app.schemas.emailConfigurations import EmailConfigurationCreate, EmailConfigurationUpdate

class EmailConfigurationRepository(BaseRepository[EmailConfiguration, EmailConfigurationCreate, EmailConfigurationUpdate]):
    """
    Repository for EmailConfiguration operations.
    Extends the base repository with email configuration-specific operations.
    """
    
    def get_by_user_id(
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
        return db.query(self.model).filter(
            self.model.user_id == user_id
        ).offset(skip).limit(limit).all()
    
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
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.is_active == True
            )
        ).all()
    
    def get_by_name(
        self, 
        db: Session, 
        *, 
        user_id: int,
        configuration_name: str
    ) -> Optional[EmailConfiguration]:
        """
        Get an email configuration by name for a user.
        
        Args:
            db: Database session
            user_id: User ID
            configuration_name: Configuration name
            
        Returns:
            Optional[EmailConfiguration]: Email configuration if found, None otherwise
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.configuration_name == configuration_name
            )
        ).first()
    
    def get_by_email(
        self, 
        db: Session, 
        *, 
        user_id: int,
        email_from: str
    ) -> Optional[EmailConfiguration]:
        """
        Get an email configuration by from email for a user.
        
        Args:
            db: Database session
            user_id: User ID
            email_from: From email address
            
        Returns:
            Optional[EmailConfiguration]: Email configuration if found, None otherwise
        """
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.email_from == email_from
            )
        ).first()
    
    def get_default(
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
        return db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.is_default == True
            )
        ).first()
    
    def set_default(
        self, 
        db: Session, 
        *, 
        email_configuration_id: int,
        user_id: int
    ) -> EmailConfiguration:
        """
        Set an email configuration as default for a user.
        This will unset any existing default configuration.
        
        Args:
            db: Database session
            email_configuration_id: ID of the configuration to set as default
            user_id: User ID
            
        Returns:
            EmailConfiguration: Updated email configuration
        """
        # Clear current default
        db.query(self.model).filter(
            and_(
                self.model.user_id == user_id,
                self.model.is_default == True
            )
        ).update({"is_default": False})
        
        # Set new default
        config = db.query(self.model).filter(self.model.id == email_configuration_id).first()
        config.is_default = True
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

# Create singleton instance
email_configuration_repository = EmailConfigurationRepository(EmailConfiguration) 