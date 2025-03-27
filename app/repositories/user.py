from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.repositories.base import BaseRepository
from app.models.users import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for User model with additional user-specific operations.
    """
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User's email
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: User's username
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email_or_username(
        self, 
        db: Session, 
        *, 
        email: Optional[str] = None, 
        username: Optional[str] = None
    ) -> Optional[User]:
        """
        Get a user by email or username.
        
        Args:
            db: Database session
            email: User's email
            username: User's username
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        if not email and not username:
            return None
            
        filters = []
        if email:
            filters.append(User.email == email)
        if username:
            filters.append(User.username == username)
            
        return db.query(User).filter(or_(*filters)).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            db: Database session
            obj_in: User creation schema
            
        Returns:
            User: Created user
        """
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            business_name=obj_in.business_name,
            phone_number=obj_in.phone_number,
            is_active=obj_in.is_active
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: User, 
        obj_in: UserUpdate | Dict[str, Any]
    ) -> User:
        """
        Update a user, handling password hashing if password is updated.
        
        Args:
            db: Database session
            db_obj: Existing user
            obj_in: Update data
            
        Returns:
            User: Updated user
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # Handle password hashing
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
            
        # Handle phone_number specially due to encryption
        # The property setter needs to be explicitly called for encryption to work
        if "phone_number" in update_data:
            phone_number = update_data.pop("phone_number")
            db_obj.phone_number = phone_number
            
        # Update remaining fields using standard approach
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
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
        return (
            db.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_superusers(self, db: Session) -> List[User]:
        """
        Get all superusers.
        
        Args:
            db: Database session
            
        Returns:
            List[User]: List of superusers
        """
        return db.query(User).filter(User.is_superuser == True).all()
    
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
        """
        user = self.get(db, id=user_id)
        if not user:
            return None
            
        if service_type == 'sms':
            user.sms_count += 1
        elif service_type == 'whatsapp':
            user.whatsapp_count += 1
            
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

# Create singleton instance
user_repository = UserRepository() 