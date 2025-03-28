from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        example="Acme Corporation",
        description="Client's full name or company name"
    )
    email: Optional[EmailStr] = Field(
        None, 
        example="contact@acmecorp.com",
        description="Client's email address for communications"
    )
    phone_number: Optional[str] = Field(
        None, 
        max_length=20, 
        example="+1234567890",
        description="Client's phone number in international format with optional + prefix"
    )
    address: Optional[str] = Field(
        None, 
        max_length=500, 
        example="123 Business Ave, Suite 100, New York, NY 10001",
        description="Client's physical address"
    )
    notes: Optional[str] = Field(
        None, 
        example="Key client in the financial sector. Prefers email communication.",
        description="Additional notes about the client"
    )
    is_active: bool = Field(
        True, 
        example=True,
        description="Whether the client is active (true) or archived (false)"
    )

class ClientCreate(ClientBase):
    """Schema for creating a new client record"""
    pass

class ClientUpdate(BaseModel):
    """Schema for updating an existing client record"""
    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255, 
        example="Acme Corporation Updated",
        description="Updated client name"
    )
    email: Optional[EmailStr] = Field(
        None, 
        example="new-contact@acmecorp.com",
        description="Updated email address"
    )
    phone_number: Optional[str] = Field(
        None, 
        max_length=20, 
        example="+1987654321",
        description="Updated phone number"
    )
    address: Optional[str] = Field(
        None, 
        max_length=500, 
        example="456 New Address Blvd, Suite 200, San Francisco, CA 94107",
        description="Updated physical address"
    )
    notes: Optional[str] = Field(
        None, 
        example="Client has new management. Now prefers phone calls over emails.",
        description="Updated notes about the client"
    )
    is_active: Optional[bool] = Field(
        None, 
        example=True,
        description="Set to false to archive the client"
    )

class ClientInDBBase(ClientBase):
    """Base schema for a client in database with system fields"""
    id: int = Field(..., example=1, description="Unique identifier for the client")
    user_id: int = Field(..., example=42, description="ID of the user who owns this client")
    created_at: datetime = Field(..., example="2023-01-15T14:30:00Z", description="When the client was created")
    updated_at: Optional[datetime] = Field(None, example="2023-02-20T09:15:00Z", description="When the client was last updated")

    model_config = ConfigDict(from_attributes=True)

class Client(ClientInDBBase):
    """Complete client model returned from API"""
    pass

class ClientDetail(Client):
    """Client model with additional statistics about related records"""
    reminders_count: int = Field(0, example=5, description="Total number of reminders for this client")
    active_reminders_count: int = Field(0, example=3, description="Number of active reminders for this client")
    notifications_count: int = Field(0, example=12, description="Total number of notifications sent to this client")