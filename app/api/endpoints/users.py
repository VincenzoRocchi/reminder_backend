from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_current_active_superuser
from app.core.security import get_password_hash
from app.database import get_db
from app.models.users import User as UserModel
from app.schemas.user import User, UserCreate, UserUpdate, UserWithRelations

router = APIRouter()

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
    db_user_email = db.query(UserModel).filter(UserModel.email == user_in.email).first()
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user_username = db.query(UserModel).filter(UserModel.username == user_in.username).first()
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # If username is being updated, check if it's already taken
    if "username" in update_data and update_data["username"] != user.username:
        if db.query(UserModel).filter(UserModel.username == update_data["username"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        db.delete(user)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
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
    if db.query(UserModel).filter(UserModel.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(UserModel).filter(UserModel.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return user