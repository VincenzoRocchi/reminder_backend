from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional
from datetime import datetime

class EmailConfigurationBase(BaseModel):
    configuration_name: str = Field(..., min_length=2, max_length=255)
    smtp_host: str = Field(..., min_length=1, max_length=255)
    smtp_port: int = Field(..., ge=1, le=65535)
    smtp_user: str = Field(..., min_length=1, max_length=255)
    smtp_password: Optional[str] = None
    email_from: EmailStr = Field(...)
    is_active: bool = True

class EmailConfigurationCreate(EmailConfigurationBase):
    """Schema for creating an email configuration"""
    smtp_password: str = Field(..., min_length=8)

class EmailConfigurationUpdate(BaseModel):
    """Schema for updating an email configuration"""
    configuration_name: Optional[str] = Field(None, min_length=2, max_length=255)
    smtp_host: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_port: Optional[int] = Field(None, ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, min_length=1, max_length=255)
    smtp_password: Optional[str] = Field(None, min_length=8)
    email_from: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class EmailConfigurationInDBBase(EmailConfigurationBase):
    """Base schema for an email configuration in database"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Don't return the password
    smtp_password: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class EmailConfiguration(EmailConfigurationInDBBase):
    """Complete email configuration model returned from API"""
    pass