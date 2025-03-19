from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Base User schema with shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = True


# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


# Schema for updating a user
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


# Schema for user in DB
class UserInDBBase(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Schema for returning user data
class User(UserInDBBase):
    pass


# Schema for user with password (for internal use)
class UserInDB(UserInDBBase):
    hashed_password: str