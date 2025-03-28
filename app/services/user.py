from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.user import user_repository
from app.schemas.user import UserCreate, UserUpdate, User
from app.core.security import verify_password
from app.core.exceptions import UserNotFoundError, UserAlreadyExistsError, InvalidCredentialsError
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import emit_event_safely, with_event_emission
from app.events.definitions.user_events import (
    create_user_created_event,
    create_user_updated_event,
    create_user_deleted_event
)

class UserService:
    """
    Service layer for User operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = user_repository
    
    @handle_exceptions(error_message="Failed to get user")
    def get_user(self, db: Session, user_id: int) -> User:
        """
        Get a user by ID.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User: User object
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = self.repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user
    
    @handle_exceptions(error_message="Failed to get user by email")
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User's email
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return self.repository.get_by_email(db, email=email)
    
    @handle_exceptions(error_message="Failed to get user by username")
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: User's username
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return self.repository.get_by_username(db, username=username)
    
    @handle_exceptions(error_message="Failed to authenticate user")
    def authenticate(self, db: Session, *, username: str = None, email: str = None, password: str) -> User:
        """
        Authenticate a user using username/email and password.
        
        Args:
            db: Database session
            username: Optional username
            email: Optional email
            password: User's password
            
        Returns:
            User: Authenticated user
            
        Raises:
            InvalidCredentialsError: If authentication fails
        """
        if not username and not email:
            raise InvalidCredentialsError("Either username or email must be provided")
            
        user = None
        if username:
            user = self.repository.get_by_username(db, username=username)
        elif email:
            user = self.repository.get_by_email(db, email=email)
            
        if not user:
            raise InvalidCredentialsError()
            
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
            
        return user
    
    @with_transaction
    @handle_exceptions(error_message="Failed to create user")
    @with_event_emission(lambda service, db, user_in, result: create_user_created_event(
        user_id=result.id,
        username=result.username,
        email=result.email,
        is_active=result.is_active,
        is_superuser=result.is_superuser,
        business_name=result.business_name
    ))
    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_in: User creation schema
            
        Returns:
            User: Created user
            
        Raises:
            UserAlreadyExistsError: If user with same email/username exists
        """
        # Check if user with same email exists
        if self.repository.get_by_email(db, email=user_in.email):
            raise UserAlreadyExistsError(f"User with email {user_in.email} already exists")
            
        # Check if user with same username exists
        if self.repository.get_by_username(db, username=user_in.username):
            raise UserAlreadyExistsError(f"User with username {user_in.username} already exists")
        
        # Create the user
        created_user = self.repository.create(db, obj_in=user_in)
        
        return created_user
    
    @with_transaction
    @handle_exceptions(error_message="Failed to update user")
    @with_event_emission(lambda service, db, user_id, user_in, result: create_user_updated_event(
        user_id=result.id,
        username=result.username,
        email=result.email,
        is_active=result.is_active,
        is_superuser=result.is_superuser,
        business_name=result.business_name
    ))
    def update_user(self, db: Session, *, user_id: int, user_in: UserUpdate) -> User:
        """
        Update an existing user.
        
        Args:
            db: Database session
            user_id: User ID
            user_in: User update schema
            
        Returns:
            User: Updated user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = self.repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Update the user
        updated_user = self.repository.update(db, db_obj=user, obj_in=user_in)
        
        return updated_user
    
    @with_transaction
    @handle_exceptions(error_message="Failed to delete user")
    @with_event_emission(lambda service, db, user_id, result: create_user_deleted_event(
        user_id=user_id,
        username=result.username,
        email=result.email
    ))
    def delete_user(self, db: Session, *, user_id: int) -> User:
        """
        Delete a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User: Deleted user
            
        Raises:
            UserNotFoundError: If user not found
        """
        user = self.repository.get(db, id=user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        
        # Delete the user
        deleted_user = self.repository.delete(db, id=user_id)
        
        return deleted_user
    
    @handle_exceptions(error_message="Failed to get all users")
    def get_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of users
        """
        return self.repository.get_multi(db, skip=skip, limit=limit)
    
    def get_active_users(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[User]:
        """
        Get all active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of active users
        """
        return self.repository.get_active_users(db, skip=skip, limit=limit)
    
    def get_all_users(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Get all users regardless of active status.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of all users
        """
        return self.repository.get_multi(db, skip=skip, limit=limit)
    
    def get_superusers(self, db: Session) -> List[User]:
        """
        Get all superusers.
        
        Args:
            db: Database session
            
        Returns:
            List[User]: List of superusers
        """
        return self.repository.get_superusers(db)
    
    def increment_usage_count(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        service_type: str
    ) -> User:
        """
        Increment usage count for a specific service.
        
        Args:
            db: Database session
            user_id: User ID
            service_type: Type of service ('sms' or 'whatsapp')
            
        Returns:
            User: Updated user
            
        Raises:
            UserNotFoundError: If user not found
            ValueError: If service_type is invalid
        """
        if service_type not in ['sms', 'whatsapp']:
            raise ValueError("service_type must be 'sms' or 'whatsapp'")
            
        user = self.get_user(db, user_id)
        return self.repository.increment_usage_count(
            db, 
            user_id=user_id, 
            service_type=service_type
        )

# Create singleton instance
user_service = UserService() 