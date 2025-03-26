from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_current_active_superuser
from app.core.security import get_password_hash
from app.database import get_db
from app.models.users import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate, UserWithRelations
from app.core.exceptions import AppException,InsufficientPermissionsError, SecurityException, DatabaseError

router = APIRouter()

# Helper function to reduce code duplication
def check_user_exists(db: Session, email: str = None, username: str = None):
    """Check if a user with the given email or username already exists"""
    if email:
        db_user = db.query(UserModel).filter(UserModel.email == email).first()
        if db_user:
            raise AppException(
                message="Email already registered",
                code="EMAIL_ALREADY_EXISTS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    if username:
        db_user = db.query(UserModel).filter(UserModel.username == username).first()
        if db_user:
            raise AppException(
                message="Username already taken",
                code="USERNAME_ALREADY_EXISTS",
                status_code=status.HTTP_400_BAD_REQUEST
            )

@router.get("/", response_model=List[User])
async def read_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve users. Only superusers can access this endpoint.
    """
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Create new user. Only superusers can create new users.
    """
    # Check if user with this email or username exists
    check_user_exists(db, email=user_in.email, username=user_in.username)
    
    # Create the user
    user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        business_name=user_in.business_name,
        phone_number=user_in.phone_number,
        is_active=user_in.is_active,
        is_superuser=False,
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
        
    return user

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get current user information.
    """
    return current_user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific user by id.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise AppException(
            message="User not found",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: Annotated[UserUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a user.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise AppException(
            message="User not found",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    # Update fields
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Handle password separately
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password
    
    # If email is being updated, check if it's already taken
    if "email" in update_data and update_data["email"] != user.email:
        if db.query(UserModel).filter(UserModel.email == update_data["email"]).first():
            raise AppException(
                message="Email already registered",
                code="EMAIL_ALREADY_EXISTS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # If username is being updated, check if it's already taken
    if "username" in update_data and update_data["username"] != user.username:
        if db.query(UserModel).filter(UserModel.username == update_data["username"]).first():
            raise AppException(
                message="Username already taken",
                code="USERNAME_ALREADY_EXISTS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Delete a user. Only superusers can delete users.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise AppException(
            message="User not found",
            code="USER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return {"detail": "User deleted successfully"}

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user without requiring existing authentication.
    """
    # Check if user with this email or username exists
    check_user_exists(db, email=user_in.email, username=user_in.username)
    
    # Create the user
    user = UserModel(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        business_name=user_in.business_name,
        phone_number=user_in.phone_number,
        is_active=True,
        is_superuser=False,
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return user