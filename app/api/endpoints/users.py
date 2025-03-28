from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_current_active_superuser, get_current_user_allow_inactive
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate, UserWithRelations, UserStatusUpdate
from app.core.exceptions import AppException, InsufficientPermissionsError, SecurityException, DatabaseError
from app.services.user import user_service

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

@router.get("/active", response_model=List[User])
async def read_active_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve active users only. Only superusers can access this endpoint.
    """
    return user_service.get_active_users(db, skip=skip, limit=limit)

@router.get("/all", response_model=List[User])
async def read_all_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all users including inactive ones. Only superusers can access this endpoint.
    """
    return user_service.get_all_users(db, skip=skip, limit=limit)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Create new user. Only superusers can create new users.
    """
    return user_service.create_user(db, user_in=user_in)

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
    user = user_service.get_user(db, user_id=user_id)
    
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
    user = user_service.get_user(db, user_id=user_id)
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    return user_service.update_user(db, user_id=user_id, user_in=user_in)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Delete a user. Only superusers can delete users.
    """
    user_service.delete_user(db, user_id=user_id)
    return {"detail": "User deleted successfully"}

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user without requiring existing authentication.
    """
    return user_service.create_user(db, user_in=user_in)

@router.patch("/{user_id}/status", response_model=User)
async def update_user_status(
    user_id: int,
    status_update: Annotated[UserStatusUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user_allow_inactive)],
):
    """
    Update a user's active status.
    
    This endpoint allows setting a user's active status explicitly,
    which is more specific than the general update endpoint.
    
    Regular users can only modify their own status, while
    superusers can modify any user's status.
    
    Special note: This endpoint is accessible to inactive users
    so they can reactivate their accounts.
    """
    user = user_service.get_user(db, user_id=user_id)
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    return user_service.update_user_status(db, user_id=user_id, is_active=status_update.is_active)