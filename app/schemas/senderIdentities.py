from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

class IdentityType(str, Enum):
    PHONE = "PHONE"
    EMAIL = "EMAIL"

class SenderIdentityBase(BaseModel):
    identity_type: IdentityType
    value: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    is_default: bool = False

class SenderIdentityCreate(SenderIdentityBase):
    """Schema for creating a sender identity"""
    pass

class SenderIdentityUpdate(BaseModel):
    """Schema for updating a sender identity"""
    value: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_default: Optional[bool] = None

class SenderIdentityInDBBase(SenderIdentityBase):
    """Base schema for a sender identity in database"""
    id: int
    user_id: int
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SenderIdentity(SenderIdentityInDBBase):
    """Complete sender identity model returned from API"""
    pass