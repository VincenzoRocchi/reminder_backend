from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.core.settings import settings
from app.core.security import verify_password, get_signing_key
from app.models.users import User
from app.database import get_db
from app.core import request_context
from app.core.token_blacklist import is_token_blacklisted
from app.core.exceptions import TokenInvalidError, TokenExpiredError, UserNotFoundError

# Configure logger
logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
):
    """
    Get the current user from the token.
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User object if token is valid
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
        
        # Store user ID in the request context
        request_context.set_user_id(int(user_id))
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            logger.warning(f"User with ID {user_id} from token not found in database")
            raise UserNotFoundError()
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Inactive user {user_id} attempted to access protected endpoint")
            raise UserNotFoundError("User is inactive")
        
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


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User email
        password: User password
        
    Returns:
        User object if authentication successful, False otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user