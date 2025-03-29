from typing import Optional
from pydantic import BaseModel, Field

class TokenData(BaseModel):
    """Internal schema for token claims extraction"""
    sub: Optional[str] = Field(
        None,
        example="1",
        description="Subject identifier (usually the user ID)"
    )

class TokenPayload(BaseModel):
    """Schema representing JWT payload structure"""
    sub: str = Field(
        ...,
        example="1",
        description="Subject identifier (usually the user ID)"
    )
    exp: int = Field(
        ...,
        example=1672531200,
        description="Expiration timestamp (Unix time)"
    )
    jti: str = Field(
        ...,
        example="5f8d94c1-e866-4a84-b3cc-bc39146d6963",
        description="JWT unique identifier used for token blacklisting"
    )
    token_type: str = Field(
        ...,
        example="access",
        description="Token type (access or refresh)"
    )

class Token(BaseModel):
    """Response schema for successful authentication"""
    access_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT access token used for authenticating API requests"
    )
    token_type: str = Field(
        "bearer",
        example="bearer",
        description="Token type (always 'bearer' for OAuth2 compatibility)"
    )
    refresh_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT refresh token used to obtain new access tokens without re-authentication"
    )

class TokenRefresh(BaseModel):
    """Request schema for refreshing access token"""
    refresh_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT refresh token obtained during login (typically valid for 7 days)"
    )

class PasswordResetRequest(BaseModel):
    """Request schema for initiating password reset"""
    email: str = Field(
        ...,
        example="user@example.com",
        description="Email address associated with the account"
    )

class PasswordReset(BaseModel):
    """Request schema for completing password reset"""
    token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="Password reset token received by email (valid for limited time)"
    )
    new_password: str = Field(
        ...,
        example="secureNewP@ssword123",
        description="New password (minimum 8 characters, should meet security requirements)"
    )

class TokenVerifyResponse(BaseModel):
    """Response schema for token verification"""
    valid: bool = Field(
        ...,
        example=True,
        description="Whether the token is valid and not blacklisted"
    )
    user_id: Optional[str] = Field(
        None,
        example="1",
        description="The user ID contained in the token (if valid)"
    )