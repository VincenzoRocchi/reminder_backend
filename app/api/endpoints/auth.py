from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

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
from app.schemas.token import Token
from app.schemas.user import User
from app.models.users import User as UserModel

router = APIRouter()

@router.post("/login", response_model=Token, dependencies=[Depends(rate_limit_login)])
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests
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


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
):
    """
    Logout by blacklisting the current token
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
def refresh_token(
    db: Session = Depends(get_db), refresh_token: str = Body(...)
):
    """
    Get a new access token using refresh token
    """
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
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user


@router.post("/verify-token")
def verify_token(
    token: str = Body(...),
):
    """
    Verify if a token is valid and not blacklisted
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