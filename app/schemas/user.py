from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
import re
from app.core.exceptions import ValidationError

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255, example="johndoe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    first_name: Optional[str] = Field(None, max_length=255, example="John")
    last_name: Optional[str] = Field(None, max_length=255, example="Doe")
    business_name: Optional[str] = Field(None, max_length=255, example="Acme Inc")
    phone_number: Optional[str] = Field(
        None, 
        max_length=20, 
        example="+1234567890",
        description="Phone number in international format with optional + prefix. Must be 10-15 digits."
    )
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        example="securepassword123",
        description="Password must be at least 8 characters long"
    )
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is None or v == "":
            return v
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValidationError(field="phone_number", message="Must be 10-15 digits with optional + prefix")
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    business_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v):
        if v is None or v == "":
            return v
        if not re.match(r'^\+?[0-9]{10,15}$', v):
            raise ValidationError(field="phone_number", message="Must be 10-15 digits with optional + prefix")
        return v

class UserStatusUpdate(BaseModel):
    """Schema for updating a user's active status"""
    is_active: bool = Field(..., example=True, description="Set to true to activate the user, false to deactivate")

class UserInDBBase(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class User(UserInDBBase):
    """Complete user model returned from API"""
    pass

class UserWithRelations(User):
    """User model with relationships data"""
    service_accounts_count: int = 0
    clients_count: int = 0
    reminders_count: int = 0