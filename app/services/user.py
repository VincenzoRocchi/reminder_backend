from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.user import user_repository
from app.schemas.user import UserCreate, UserUpdate, User
from app.core.security import verify_password
from app.core.exceptions import UserNotFoundError, UserAlreadyExistsError, InvalidCredentialsError

class UserService:
    """
    Service layer for User operations.
    Handles business logic and uses the repository for data access.
    """
    
    def __init__(self):
        self.repository = user_repository
    
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
    
    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            db: Database session
            user_in: User creation data
            
        Returns:
            User: Created user
            
        Raises:
            UserAlreadyExistsError: If user with same email or username exists
        """
        # Check if user with same email exists
        if self.get_user_by_email(db, email=user_in.email):
            raise UserAlreadyExistsError(f"User with email {user_in.email} already exists")
            
        # Check if user with same username exists
        if self.get_user_by_username(db, username=user_in.username):
            raise UserAlreadyExistsError(f"User with username {user_in.username} already exists")
            
        return self.repository.create(db, obj_in=user_in)
    
    def update_user(
        self, 
        db: Session, 
        *, 
        user_id: int, 
        user_in: UserUpdate | Dict[str, Any]
    ) -> User:
        """
        Update a user.
        
        Args:
            db: Database session
            user_id: User ID
            user_in: Update data
            
        Returns:
            User: Updated user
            
        Raises:
            UserNotFoundError: If user not found
            UserAlreadyExistsError: If new email/username conflicts with existing user
        """
        user = self.get_user(db, user_id)
        
        # If email is being updated, check for conflicts
        if isinstance(user_in, dict):
            email = user_in.get("email")
        else:
            email = user_in.email
            
        if email and email != user.email:
            existing_user = self.get_user_by_email(db, email=email)
            if existing_user:
                raise UserAlreadyExistsError(f"User with email {email} already exists")
                
        # If username is being updated, check for conflicts
        if isinstance(user_in, dict):
            username = user_in.get("username")
        else:
            username = user_in.username
            
        if username and username != user.username:
            existing_user = self.get_user_by_username(db, username=username)
            if existing_user:
                raise UserAlreadyExistsError(f"User with username {username} already exists")
                
        return self.repository.update(db, db_obj=user, obj_in=user_in)
    
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
        user = self.get_user(db, user_id)
        return self.repository.delete(db, id=user_id)
    
    def authenticate_user(
        self, 
        db: Session, 
        *, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session
            email: User's email
            password: User's password
            
        Returns:
            Optional[User]: User if authentication successful, None otherwise
        """
        user = self.get_user_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
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