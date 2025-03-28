from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from typing import Optional
from datetime import datetime

class EmailConfigurationBase(BaseModel):
    configuration_name: str = Field(
        ..., 
        min_length=2, 
        max_length=255,
        example="Company Gmail",
        description="Friendly name for this email configuration"
    )
    smtp_host: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        example="smtp.gmail.com",
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        ..., 
        ge=1, 
        le=65535,
        example=587,
        description="SMTP server port (typically 25, 465, or 587)"
    )
    smtp_user: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        example="notifications@yourcompany.com",
        description="SMTP username for authentication"
    )
    smtp_password: Optional[str] = Field(
        None,
        description="SMTP password for authentication (not returned in API responses)"
    )
    email_from: EmailStr = Field(
        ...,
        example="notifications@yourcompany.com",
        description="Email address used as the sender"
    )
    is_active: bool = Field(
        True,
        example=True,
        description="Whether this configuration is active and available for use"
    )

class EmailConfigurationCreate(EmailConfigurationBase):
    """Schema for creating a new email configuration with authentication"""
    smtp_password: str = Field(
        ..., 
        min_length=8,
        example="secureP@ssword123",
        description="SMTP password for authentication (minimum 8 characters)"
    )

class EmailConfigurationUpdate(BaseModel):
    """Schema for updating an existing email configuration"""
    configuration_name: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=255,
        example="Updated Gmail Config",
        description="New name for the configuration"
    )
    smtp_host: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255,
        example="smtp.gmail.com",
        description="New SMTP server hostname"
    )
    smtp_port: Optional[int] = Field(
        None, 
        ge=1, 
        le=65535,
        example=465,
        description="New SMTP server port"
    )
    smtp_user: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255,
        example="new-notifications@yourcompany.com",
        description="New SMTP username"
    )
    smtp_password: Optional[str] = Field(
        None, 
        min_length=8,
        example="newSecureP@ssword456",
        description="New SMTP password (minimum 8 characters)"
    )
    email_from: Optional[EmailStr] = Field(
        None,
        example="new-notifications@yourcompany.com",
        description="New sender email address"
    )
    is_active: Optional[bool] = Field(
        None,
        example=False,
        description="Set to false to deactivate this configuration"
    )

class EmailConfigurationInDBBase(EmailConfigurationBase):
    """Base schema for an email configuration stored in the database with system fields"""
    id: int = Field(
        ...,
        example=1,
        description="Unique identifier for this email configuration"
    )
    user_id: int = Field(
        ...,
        example=42,
        description="ID of the user who owns this configuration"
    )
    created_at: datetime = Field(
        ...,
        example="2023-01-15T10:30:00Z",
        description="When this configuration was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        example="2023-02-20T15:45:00Z",
        description="When this configuration was last updated"
    )
    
    # Don't return the password
    smtp_password: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class EmailConfiguration(EmailConfigurationInDBBase):
    """Complete email configuration model returned from API (without password)"""
    pass