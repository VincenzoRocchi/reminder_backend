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
    
    # Email notification settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # SMS notification settings (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # WhatsApp notification settings
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None


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
    
    # Email notification settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # SMS notification settings (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # WhatsApp notification settings
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None


# Schema for notification settings update
class BusinessNotificationSettings(BaseModel):
    # Email notification settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # SMS notification settings (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # WhatsApp notification settings
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None


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