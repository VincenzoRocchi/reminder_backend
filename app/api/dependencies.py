from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import get_db_session as get_db
from app.core.settings import settings
from app.models.users import User
from app.schemas.token import TokenPayload
from app.core.security import get_signing_key
from app.core.token_blacklist import is_token_blacklisted
from app.core.exceptions import TokenInvalidError, TokenExpiredError, UserNotFoundError

from app.core.auth import get_current_user
import logging
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User object if current user is a superuser
        
    Raises:
        HTTPException: If current user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
    
async def get_current_user_allow_inactive(
    request: Request,
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
):
    """
    Get the current user from the token, allowing inactive users.
    
    This special dependency is for endpoints that need to be accessible
    by inactive users, such as the status update endpoint where users
    can reactivate their accounts.
    
    Args:
        request: FastAPI request object
        db: Database session
        token: JWT token
        
    Returns:
        User object if token is valid, regardless of active status
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            logger.warning("Attempt to use blacklisted token")
            raise TokenInvalidError("Token has been revoked")
        
        # Decode token
        payload = jwt.decode(
            token, get_signing_key(), algorithms=[settings.ALGORITHM]
        )
        
        # Check token expiration
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp) < datetime.now():
            logger.warning("Attempt to use expired token")
            raise TokenExpiredError()
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing 'sub' claim")
            raise TokenInvalidError("Invalid token format")
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User with ID {user_id} from token not found in database")
            raise UserNotFoundError()
        
        # Log if the user is inactive
        if not user.is_active:
            # Only log as info since we're allowing inactive users
            logger.info(f"Inactive user {user_id} accessing {request.url.path}")
        
        return user
    
    except (TokenInvalidError, TokenExpiredError, UserNotFoundError) as e:
        # Convert app exceptions to HTTP exceptions
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        # Log and convert JWT errors
        logger.warning(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )