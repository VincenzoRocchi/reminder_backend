from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    is_active: bool = True

class ClientCreate(ClientBase):
    """Schema for creating a client"""
    pass

class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ClientInDBBase(ClientBase):
    """Base schema for a client in database"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Client(ClientInDBBase):
    """Complete client model returned from API"""
    pass

class ClientDetail(Client):
    """Client model with additional statistics"""
    reminders_count: int = 0
    active_reminders_count: int = 0
    notifications_count: int = 0