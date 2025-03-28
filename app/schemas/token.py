from typing import Optional
from pydantic import BaseModel, Field

class TokenData(BaseModel):
    sub: Optional[str] = Field(
        None,
        example="1",
        description="Subject identifier (usually the user ID)"
    )

class TokenPayload(BaseModel):
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
    type: Optional[str] = Field(
        None,
        example="access",
        description="Token type (access or refresh)"
    )

class Token(BaseModel):
    access_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT access token"
    )
    token_type: str = Field(
        "bearer",
        example="bearer",
        description="Token type (always 'bearer')"
    )
    refresh_token: Optional[str] = Field(
        None,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT refresh token for obtaining new access tokens"
    )

class TokenRefresh(BaseModel):
    refresh_token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="JWT refresh token obtained during login"
    )

class PasswordReset(BaseModel):
    token: str = Field(
        ...,
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        description="Password reset token received by email"
    )
    new_password: str = Field(
        ...,
        example="secureNewP@ssword123",
        description="New password (minimum 8 characters)"
    )