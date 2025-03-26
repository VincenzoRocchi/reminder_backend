from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
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

# Create singleton instance
email_configuration_repository = EmailConfigurationRepository(EmailConfiguration) 