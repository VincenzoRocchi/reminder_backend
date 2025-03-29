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
    Retrieve a list of all active users in the system.
    
    This endpoint:
    - Returns all users with is_active=True
    - Supports pagination with skip and limit parameters
    - Returns basic user information excluding sensitive data
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    
    Notes:
    - Restricted to superusers only
    - Useful for admin dashboards and user management interfaces
    """
    return user_service.get_active_users(db, skip=skip, limit=limit)

@router.get("/admin/all", response_model=List[User])
async def read_all_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve a list of all users in the system, including inactive accounts.
    
    This endpoint:
    - Returns all users regardless of their active status
    - Supports pagination with skip and limit parameters
    - Returns basic user information excluding sensitive data
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return
    
    Notes:
    - Restricted to superusers only
    - Intended for administrative purposes only
    - Includes deactivated/suspended accounts
    """
    return user_service.get_all_users(db, skip=skip, limit=limit)

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Create a new user account by an administrator.
    
    This endpoint:
    - Creates a new user with the provided details
    - Securely hashes the password before storage
    - Returns the created user object without the password
    
    Required fields:
    - username: Unique username (3-255 characters)
    - email: Valid email address
    - password: Secure password (minimum 8 characters)
    
    Optional fields:
    - first_name: User's first name
    - last_name: User's last name
    - business_name: Company or organization name
    - phone_number: Contact phone number in international format
    - is_active: Whether the account should be active immediately
    
    Notes:
    - Restricted to superusers only
    - For self-registration, users should use the /register endpoint instead
    - Usernames and emails are checked for uniqueness
    """
    return user_service.create_user(db, user_in=user_in)

@router.get("/me", response_model=User)
async def read_user_me(
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get the profile information of the currently authenticated user.
    
    This endpoint:
    - Returns the full profile of the authenticated user
    - Does not require any parameters as it uses the authentication token
    
    Notes:
    - Requires a valid access token in the Authorization header
    - Commonly used for profile pages and account management
    - Available to all authenticated users
    """
    return current_user

@router.get("/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get detailed information about a specific user by their ID.
    
    This endpoint:
    - Returns the full profile of the requested user
    - Performs permission checking (users can only view their own profile unless they're superusers)
    
    Parameters:
    - user_id: The unique identifier of the user to retrieve
    
    Notes:
    - Regular users can only access their own profile
    - Superusers can access any user's profile
    - Returns 404 if the user doesn't exist
    - Returns 403 if permission check fails
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
    Update a user's profile information.
    
    This endpoint:
    - Updates the specified fields of a user's profile
    - Applies permission checks (users can only update their own profile unless they're superusers)
    - Returns the updated user profile
    
    Parameters:
    - user_id: The unique identifier of the user to update
    
    Available fields to update:
    - username: New unique username
    - email: New email address
    - password: New password (will be hashed)
    - first_name: Updated first name
    - last_name: Updated last name
    - business_name: Updated company/organization name
    - phone_number: Updated phone number
    - is_active: Account status (superusers only)
    
    Notes:
    - All fields are optional - only specified fields will be updated
    - If changing password, it will be securely hashed
    - Regular users can only update their own profile
    - Superusers can update any user's profile
    - Returns 404 if the user doesn't exist
    - Returns 403 if permission check fails
    """
    user = user_service.get_user(db, user_id=user_id)
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    return user_service.update_user(db, user_id=user_id, user_in=user_in)

@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    Permanently delete a user account from the system.
    
    This endpoint:
    - Completely removes the user and all associated data from the database
    - Performs permission checks (restricted to superusers only)
    
    Parameters:
    - user_id: The unique identifier of the user to delete
    
    Notes:
    - This is a destructive operation that cannot be undone
    - Consider using the status update endpoint to deactivate accounts instead
    - Restricted to superusers only
    - Returns 404 if the user doesn't exist
    """
    user_service.delete_user(db, user_id=user_id)
    return {"detail": "User deleted successfully"}

@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: Annotated[UserCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Register a new user account (self-registration).
    
    This endpoint:
    - Creates a new user account based on the provided information
    - Securely hashes the password before storage
    - Returns the created user object without the password
    - Does not require authentication (open endpoint)
    
    Required fields:
    - username: Unique username (3-255 characters)
    - email: Valid email address
    - password: Secure password (minimum 8 characters)
    
    Optional fields:
    - first_name: User's first name
    - last_name: User's last name
    - business_name: Company or organization name
    - phone_number: Contact phone number in international format
    
    Notes:
    - Open to the public - no authentication required
    - Usernames and emails are checked for uniqueness
    - Email verification may be required depending on system configuration
    - In production, consider adding CAPTCHA or other anti-spam measures
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
    Update a user's active status (activate or deactivate account).
    
    This endpoint:
    - Sets a user's active status to true (activate) or false (deactivate)
    - Performs permission checks (users can only update their own status unless they're superusers)
    - Returns the updated user profile
    
    Parameters:
    - user_id: The unique identifier of the user to update
    
    Required fields:
    - is_active: Boolean indicating whether the account should be active
    
    Notes:
    - Regular users can only update their own status
    - Superusers can update any user's status
    - This endpoint is accessible to inactive users so they can reactivate their accounts
    - Deactivating an account is reversible (unlike deletion)
    - A common use case is for users to temporarily disable their account
    """
    user = user_service.get_user(db, user_id=user_id)
    
    # Only allow updating yourself or if you're admin
    if user.id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError(required_permission="superuser")
    
    return user_service.update_user_status(db, user_id=user_id, is_active=status_update.is_active)