from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_current_active_superuser
from app.core.security import get_password_hash
from app.database import get_db
from app.models.users import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Retrieve users. Only superusers can access this endpoint.
    """
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users


@router.post("/", response_model=User)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_superuser),
):
    """
    Create new user. Only superusers can create new users.
    """
    # Check if the user with this email exists
    db_user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    
    # Create the user
    user = UserModel(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        phone_number=user_in.phone_number,
        is_active=user_in.is_active,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a specific user by id.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user == current_user or current_user.is_superuser:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions to access this user",
    )


@router.put("/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update a user.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Only allow updating your own user or if you're a superuser
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user",
        )
    
    # Update the user
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.phone_number is not None:
        user.phone_number = user_in.phone_number
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    if user_in.is_active is not None and current_user.is_superuser:
        user.is_active = user_in.is_active
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=User)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user without requiring existing authentication.
    """
    # Check if the user with this email exists
    db_user = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system",
        )
    
    # Create the user
    user = UserModel(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        phone_number=user_in.phone_number,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user