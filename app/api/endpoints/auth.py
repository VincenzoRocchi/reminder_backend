from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Annotated

from app.core.rate_limiter import rate_limit_login
from app.api.dependencies import get_current_user, oauth2_scheme
from app.core.auth import authenticate_user
from app.core.security import create_access_token, create_refresh_token, get_signing_key
from app.core.settings import settings
from app.core.exceptions import (
    TokenExpiredError, 
    TokenInvalidError, 
    AppException,
    SecurityException
)
from app.core.token_blacklist import token_blacklist
from app.database import get_db_session as get_db
from app.schemas.token import Token, TokenRefresh
from app.schemas.user import User
from app.models.users import User as UserModel

router = APIRouter()

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_login)])
async def login(
    db: Annotated[Session, Depends(get_db)], 
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    Log in with username and password to get access and refresh tokens.
    
    This endpoint implements OAuth2 password flow compatible with standard OAuth clients.
    
    On successful authentication:
    - Returns an access token (short-lived, typically 30 minutes)
    - Returns a refresh token (longer-lived, typically 7 days) 
    - Both tokens are JWT format
    
    Notes:
    - Username can be either the user's username or email address
    - Rate limiting is applied to prevent brute force attacks
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise AppException(
            message="Incorrect username or password",
            error_code="INVALID_CREDENTIALS",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    return {
        "access_token": create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "refresh_token": create_refresh_token(
            data={"sub": str(user.id)}, expires_delta=refresh_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Log out by invalidating the current access token.
    
    This endpoint:
    - Extracts the token's unique identifier (jti) and expiration time
    - Adds the token to a blacklist until its original expiration time
    - Future requests with this token will be rejected
    
    Notes:
    - Requires a valid access token in the Authorization header
    - The token blacklist is temporary and cleaned up periodically
    - For complete security, clients should also discard the refresh token
    """
    try:
        payload = jwt.decode(
            token, get_signing_key(), algorithms=[settings.ALGORITHM]
        )
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp)
            token_blacklist.add_token(jti, expires_at)
            
        return {"detail": "Successfully logged out"}
    except JWTError:
        raise TokenInvalidError(message="Could not decode token")


@router.post("/refresh", response_model=Token)
async def refresh(
    db: Annotated[Session, Depends(get_db)], 
    refresh_token_data: Annotated[TokenRefresh, Body(...)]
):
    """
    Get a new access token using a refresh token.
    
    This endpoint:
    - Validates the provided refresh token
    - Issues a new access token if the refresh token is valid
    - Returns the same refresh token for continued use
    
    Required fields:
    - refresh_token: The refresh token obtained during login
    
    Notes:
    - Use this endpoint when your access token has expired
    - The refresh token has a longer lifetime than access tokens
    - If the refresh token is invalid or expired, you must log in again
    """
    refresh_token = refresh_token_data.refresh_token
    
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("token_type")
        
        if user_id is None or token_type != "refresh":
            raise TokenInvalidError(message="Invalid token type or missing user ID")
    except JWTError:
        raise TokenInvalidError(message="Could not decode token")
    
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise AppException(
            message="User not found",
            error_code="USER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "refresh_token": refresh_token,  # Return the same refresh token
        "token_type": "bearer",
    }


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Get information about the currently authenticated user.
    
    This endpoint:
    - Retrieves the user profile associated with the access token
    - Returns user details like ID, username, email, etc.
    
    Notes:
    - Requires a valid access token in the Authorization header
    - The token's subject (sub) claim is used to identify the user
    - Useful for frontend applications to get the logged-in user's details
    """
    return current_user


@router.post("/verify-token", status_code=status.HTTP_200_OK)
async def verify_token(
    token: Annotated[str, Body(..., embed=True)]
):
    """
    Verify if a JWT token is valid and not blacklisted.
    
    This endpoint:
    - Decodes and validates the token's signature
    - Checks if the token is in the blacklist
    - Returns the token's validity and associated user ID
    
    Required fields:
    - token: The JWT token to verify
    
    Returns:
    - valid: Boolean indicating if the token is valid
    - user_id: The user ID extracted from the token (if valid)
    
    Notes:
    - Useful for services to verify tokens without needing to implement JWT validation
    - Can be used by API gateways or middleware for token validation
    """
    try:
        payload = jwt.decode(
            token, get_signing_key(), algorithms=[settings.ALGORITHM]
        )
        jti = payload.get("jti")
        
        if jti and token_blacklist.is_blacklisted(jti):
            raise TokenInvalidError(message="Token has been revoked")
            
        return {"valid": True, "user_id": payload.get("sub")}
    except JWTError:
        raise TokenInvalidError(message="Invalid token")
    except Exception as e:
        raise AppException(
            message=f"Error verifying token: {str(e)}",
            error_code="TOKEN_VERIFICATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )