from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
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
from app.core.error_handling import handle_exceptions
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
    @handle_exceptions(error_message="Failed to authenticate user")
    async def authenticate_user(email: str, password: str) -> User:
        """Authenticate a user by email and password."""
        user = await User.get_by_email(email)
        if not user:
            raise UserNotFoundError("User not found")
        if not AuthService.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect password")
        return user

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> str:
        """Create a new access token using a refresh token."""
        token_data = AuthService.verify_refresh_token(refresh_token)
        user = await User.get_by_id(token_data.sub)
        if not user:
            raise UserNotFoundError("User not found")
        return AuthService.create_access_token(user.id)

    @staticmethod
    async def reset_password(token: str, new_password: str) -> None:
        """Reset a user's password using a password reset token."""
        token_data = AuthService.verify_password_reset_token(token)
        user = await User.get_by_id(token_data.sub)
        if not user:
            raise UserNotFoundError("User not found")
        
        # Update password
        user.hashed_password = AuthService.get_password_hash(new_password)
        await user.save()

# Create singleton instance
auth_service = AuthService() 