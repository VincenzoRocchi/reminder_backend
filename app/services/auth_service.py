from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.settings import get_settings
from app.models.users import User
from app.schemas.token import TokenData, TokenPayload
from app.core.exceptions import (
    InvalidCredentialsError,
    TokenExpiredError,
    TokenInvalidError,
    UserNotFoundError
)
from app.core.security import verify_password
from app.core.error_handling import handle_exceptions, with_transaction
from app.events.utils import queue_event
from app.events.definitions.user_events import (
    create_user_logged_in_event,
    create_user_logged_out_event,
    create_user_password_reset_event
)
import logging

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    @staticmethod
    @handle_exceptions(error_message="Failed to create access token")
    def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
        """Create a new access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(subject: str | Any) -> str:
        """Create a new refresh token."""
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_password_reset_token(subject: str | Any) -> str:
        """Create a password reset token."""
        expire = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        to_encode = {"exp": expire, "sub": str(subject), "type": "password_reset"}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    @handle_exceptions(error_message="Failed to verify token")
    def verify_token(token: str) -> TokenPayload:
        """Verify a token and return its payload."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            token_data = TokenPayload(**payload)
            
            # Check if token is expired
            if datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
                raise TokenExpiredError("Token has expired")
            
            return token_data
        except JWTError:
            raise TokenInvalidError("Invalid token")
        except Exception as e:
            raise TokenInvalidError(f"Error verifying token: {str(e)}")

    @staticmethod
    def verify_access_token(token: str) -> TokenData:
        """Verify an access token specifically."""
        token_data = AuthService.verify_token(token)
        if token_data.type and token_data.type != "access":
            raise TokenInvalidError("Invalid token type")
        return TokenData(sub=token_data.sub)

    @staticmethod
    def verify_refresh_token(token: str) -> TokenData:
        """Verify a refresh token specifically."""
        token_data = AuthService.verify_token(token)
        if not token_data.type or token_data.type != "refresh":
            raise TokenInvalidError("Invalid token type")
        return TokenData(sub=token_data.sub)

    @staticmethod
    def verify_password_reset_token(token: str) -> TokenData:
        """Verify a password reset token specifically."""
        token_data = AuthService.verify_token(token)
        if not token_data.type or token_data.type != "password_reset":
            raise TokenInvalidError("Invalid token type")
        return TokenData(sub=token_data.sub)

    @staticmethod
    @with_transaction
    @handle_exceptions(error_message="Failed to authenticate user")
    def authenticate_user(
        db: Session, 
        *, 
        email: str, 
        password: str, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None,
        **kwargs
    ) -> User:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session
            email: User's email
            password: User's password
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string
            
        Returns:
            User: Authenticated user object
            
        Raises:
            UserNotFoundError: If user not found
            InvalidCredentialsError: If password is incorrect
        """
        # Get user by email
        from app.repositories.user import user_repository
        user = user_repository.get_by_email(db, email=email)
        
        if not user:
            # Queue failed login event
            if '_transaction_id' in kwargs:
                event = create_user_logged_in_event(
                    user_id=0,  # No user found
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
                queue_event(kwargs['_transaction_id'], event)
            
            raise UserNotFoundError("User not found")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Queue failed login event
            if '_transaction_id' in kwargs:
                event = create_user_logged_in_event(
                    user_id=user.id,
                    username=user.username,
                    email=user.email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
                queue_event(kwargs['_transaction_id'], event)
            
            raise InvalidCredentialsError("Incorrect password")
        
        # Queue successful login event
        if '_transaction_id' in kwargs:
            event = create_user_logged_in_event(
                user_id=user.id,
                username=user.username,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return user

    @staticmethod
    @with_transaction
    @handle_exceptions(error_message="Failed to log out user")
    def logout_user(
        db: Session, 
        *, 
        user_id: int, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Log out a user.
        
        Args:
            db: Database session
            user_id: User ID
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string
            
        Returns:
            bool: True if successful
        """
        # Get user by ID
        from app.repositories.user import user_repository
        user = user_repository.get(db, id=user_id)
        
        if not user:
            return False
        
        # In a real implementation, you might invalidate tokens here
        
        # Queue logout event
        if '_transaction_id' in kwargs:
            event = create_user_logged_out_event(
                user_id=user.id,
                username=user.username,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return True

    @staticmethod
    @with_transaction
    @handle_exceptions(error_message="Failed to refresh access token")
    def refresh_access_token(
        db: Session, 
        *, 
        refresh_token: str,
        **kwargs
    ) -> str:
        """
        Create a new access token using a refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token
            
        Returns:
            str: New access token
            
        Raises:
            UserNotFoundError: If user not found
            TokenInvalidError: If token is invalid
        """
        # Verify refresh token
        token_data = AuthService.verify_refresh_token(refresh_token)
        
        # Get user by ID
        from app.repositories.user import user_repository
        user = user_repository.get(db, id=int(token_data.sub))
        
        if not user:
            raise UserNotFoundError("User not found")
        
        # Create new access token
        return AuthService.create_access_token(user.id)

    @staticmethod
    @with_transaction
    @handle_exceptions(error_message="Failed to reset password")
    def reset_password(
        db: Session, 
        *, 
        token: str, 
        new_password: str, 
        ip_address: Optional[str] = None, 
        user_agent: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        Reset a user's password using a password reset token.
        
        Args:
            db: Database session
            token: Password reset token
            new_password: New password
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string
            
        Returns:
            bool: True if successful
            
        Raises:
            UserNotFoundError: If user not found
            TokenInvalidError: If token is invalid
        """
        # Verify password reset token
        token_data = AuthService.verify_password_reset_token(token)
        
        # Get user by ID
        from app.repositories.user import user_repository
        user = user_repository.get(db, id=int(token_data.sub))
        
        if not user:
            # Queue failed password reset event
            if '_transaction_id' in kwargs:
                event = create_user_password_reset_event(
                    user_id=int(token_data.sub),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False
                )
                queue_event(kwargs['_transaction_id'], event)
            
            raise UserNotFoundError("User not found")
        
        # Update password
        hashed_password = AuthService.get_password_hash(new_password)
        user_repository.update(db, db_obj=user, obj_in={"hashed_password": hashed_password})
        
        # Queue successful password reset event
        if '_transaction_id' in kwargs:
            event = create_user_password_reset_event(
                user_id=user.id,
                username=user.username,
                email=user.email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            queue_event(kwargs['_transaction_id'], event)
        
        return True

# Create singleton instance
auth_service = AuthService() 