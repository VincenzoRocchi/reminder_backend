from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# Base Business schema with shared properties
class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = True


# Schema for creating a business
class BusinessCreate(BusinessBase):
    pass


# Schema for updating a business
class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


# Schema for business in DB
class BusinessInDBBase(BusinessBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Schema for returning business data
class Business(BusinessInDBBase):
    pass