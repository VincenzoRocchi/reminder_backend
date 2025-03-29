from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, Union, Literal
from datetime import datetime
from enum import Enum

class IdentityType(str, Enum):
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    # WHATSAPP option removed - now handled by notification_type instead

# Add nested schema for creating email configuration inline
class EmailConfigurationInline(BaseModel):
    """Schema for creating an email configuration inline when creating an email sender identity"""
    name: str = Field(
        ..., 
        example="Company Gmail",
        description="Name of this email configuration"
    )
    smtp_host: str = Field(
        ..., 
        example="smtp.gmail.com",
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        ..., 
        example=587,
        description="SMTP server port"
    )
    smtp_user: str = Field(
        ..., 
        example="user@example.com",
        description="SMTP username/login"
    )
    smtp_password: str = Field(
        ..., 
        example="password123",
        description="SMTP password"
    )
    use_tls: bool = Field(
        True,
        example=True,
        description="Whether to use TLS for SMTP connection"
    )
    email_from: str = Field(
        ...,
        example="support@yourcompany.com", 
        description="From email address used for all emails sent with this configuration"
    )

class SenderIdentityBase(BaseModel):
    identity_type: IdentityType = Field(
        ...,
        example="EMAIL",
        description="Type of identity (EMAIL or PHONE)"
    )
    # We'll use field_validator to validate based on type
    email: Optional[EmailStr] = Field(
        None,
        example="support@yourcompany.com",
        description="Email address for EMAIL type identities (required if identity_type is EMAIL)"
    )
    phone_number: Optional[str] = Field(
        None, 
        example="+1234567890",
        description="Phone number for PHONE type identities (required if identity_type is PHONE)"
    )
    display_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        example="Company Support Team",
        description="Name shown to recipients when sending from this identity"
    )
    is_default: bool = Field(
        False,
        example=False,
        description="Whether this is the default identity for its type"
    )
    email_configuration_id: Optional[int] = Field(
        None,
        example=1,
        description="ID of the email configuration to use (required if identity_type is EMAIL)"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email_required_for_email_type(cls, v: Optional[EmailStr], info):
        identity_type = info.data.get('identity_type')
        if identity_type == IdentityType.EMAIL and not v:
            raise ValueError("email field is required when identity_type is EMAIL")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_required_for_phone_types(cls, v: Optional[str], info):
        identity_type = info.data.get('identity_type')
        if identity_type in [IdentityType.PHONE] and not v:
            raise ValueError(f"phone_number field is required when identity_type is {identity_type}")
        
        # Validate phone number format if provided
        if v and not v.startswith('+'):
            raise ValueError("Phone number must be in international format starting with '+'")
            
        # Simple pattern check: international format with 10-15 digits
        if v and not (v.startswith('+') and len(v) >= 10 and len(v) <= 16 and v[1:].isdigit()):
            raise ValueError("Phone number must contain 10-15 digits in international format (e.g., +1234567890)")
        
        return v
    
    @field_validator('email_configuration_id')
    @classmethod
    def validate_email_config_required_for_email_type(cls, v: Optional[int], info):
        identity_type = info.data.get('identity_type')
        if identity_type == IdentityType.EMAIL and not v:
            raise ValueError("email_configuration_id is required when identity_type is EMAIL")
        return v

# Type-specific base schemas for improved frontend experience
class EmailSenderIdentityBase(BaseModel):
    """Base schema for email sender identities with simplified fields"""
    email: EmailStr = Field(
        ...,
        example="support@yourcompany.com",
        description="Email address for this sender identity"
    )
    display_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        example="Company Support Team",
        description="Name shown to recipients when sending from this identity"
    )
    email_configuration_id: Optional[int] = Field(
        None,
        example=1,
        description="ID of the email configuration to use (optional, can be added later)"
    )
    is_default: bool = Field(
        False,
        example=False,
        description="Whether this is the default email identity"
    )

class PhoneSenderIdentityBase(BaseModel):
    """Base schema for phone sender identities with simplified fields"""
    phone_number: str = Field(
        ..., 
        example="+1234567890",
        description="Phone number in international format (e.g., +1234567890)"
    )
    display_name: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        example="Company Support",
        description="Name shown to recipients when sending from this identity"
    )
    is_default: bool = Field(
        False,
        example=False,
        description="Whether this is the default phone identity"
    )
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_format(cls, v: str):
        if not v.startswith('+'):
            raise ValueError("Phone number must be in international format starting with '+'")
            
        # Simple pattern check: international format with 10-15 digits
        if not (v.startswith('+') and len(v) >= 10 and len(v) <= 16 and v[1:].isdigit()):
            raise ValueError("Phone number must contain 10-15 digits in international format (e.g., +1234567890)")
        
        return v

class SenderIdentityCreate(SenderIdentityBase):
    """Schema for creating a new sender identity"""
    pass

class EmailSenderIdentityCreate(EmailSenderIdentityBase):
    """Schema for creating a new email sender identity"""
    email_configuration: Optional[EmailConfigurationInline] = Field(
        None,
        description="Email configuration details to create inline (alternative to email_configuration_id)"
    )

class PhoneSenderIdentityCreate(PhoneSenderIdentityBase):
    """Schema for creating a new phone sender identity"""
    pass

class SenderIdentityUpdate(BaseModel):
    """Schema for updating an existing sender identity"""
    identity_type: Optional[IdentityType] = Field(
        None,
        example="EMAIL",
        description="Updated type of identity (EMAIL or PHONE)"
    )
    email: Optional[EmailStr] = Field(
        None,
        example="new-support@yourcompany.com",
        description="Updated email address (required if changing to EMAIL type)"
    )
    phone_number: Optional[str] = Field(
        None,
        example="+1987654321",
        description="Updated phone number (required if changing to PHONE type)"
    )
    display_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255,
        example="Updated Support Team Name",
        description="Updated display name"
    )
    is_default: Optional[bool] = Field(
        None,
        example=True,
        description="Set to true to make this the default identity for its type"
    )
    email_configuration_id: Optional[int] = Field(
        None,
        example=2,
        description="Updated email configuration ID (required for EMAIL type)"
    )
    
    # Add validations for partial updates
    @field_validator('email')
    @classmethod
    def validate_email_for_updated_type(cls, v: Optional[EmailStr], info):
        identity_type = info.data.get('identity_type')
        if identity_type == IdentityType.EMAIL and v is None:
            raise ValueError("email field must be provided when updating to EMAIL type")
        return v
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_for_updated_type(cls, v: Optional[str], info):
        identity_type = info.data.get('identity_type')
        if identity_type in [IdentityType.PHONE] and v is None:
            raise ValueError(f"phone_number field must be provided when updating to {identity_type} type")
            
        # Validate phone number format if provided
        if v and not v.startswith('+'):
            raise ValueError("Phone number must be in international format starting with '+'")
            
        # Simple pattern check: international format with 10-15 digits
        if v and not (v.startswith('+') and len(v) >= 10 and len(v) <= 16 and v[1:].isdigit()):
            raise ValueError("Phone number must contain 10-15 digits in international format (e.g., +1234567890)")
        
        return v
    
    @field_validator('email_configuration_id')
    @classmethod
    def validate_email_config_for_updated_type(cls, v: Optional[int], info):
        identity_type = info.data.get('identity_type')
        if identity_type == IdentityType.EMAIL and v is None:
            raise ValueError("email_configuration_id must be provided when updating to EMAIL type")
        return v

class EmailSenderIdentityUpdate(BaseModel):
    """Schema for updating an email sender identity"""
    email: Optional[EmailStr] = Field(
        None,
        example="new-support@yourcompany.com",
        description="Updated email address"
    )
    display_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255,
        example="Updated Support Team",
        description="Updated display name"
    )
    email_configuration_id: Optional[int] = Field(
        None,
        example=2,
        description="Updated email configuration ID"
    )
    email_configuration: Optional[EmailConfigurationInline] = Field(
        None,
        description="Email configuration details to create inline (alternative to email_configuration_id)"
    )
    is_default: Optional[bool] = Field(
        None,
        example=True,
        description="Set to true to make this the default email identity"
    )

class PhoneSenderIdentityUpdate(BaseModel):
    """Schema for updating a phone sender identity"""
    phone_number: Optional[str] = Field(
        None,
        example="+1987654321",
        description="Updated phone number"
    )
    display_name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255,
        example="Updated Support Team",
        description="Updated display name"
    )
    is_default: Optional[bool] = Field(
        None,
        example=True,
        description="Set to true to make this the default phone identity"
    )
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_format(cls, v: Optional[str]):
        if v is None:
            return v
            
        if not v.startswith('+'):
            raise ValueError("Phone number must be in international format starting with '+'")
            
        # Simple pattern check: international format with 10-15 digits
        if not (v.startswith('+') and len(v) >= 10 and len(v) <= 16 and v[1:].isdigit()):
            raise ValueError("Phone number must contain 10-15 digits in international format (e.g., +1234567890)")
        
        return v

class SenderIdentityInDBBase(SenderIdentityBase):
    """Base schema for a sender identity stored in the database with system fields"""
    id: int = Field(
        ...,
        example=1,
        description="Unique identifier for this sender identity"
    )
    user_id: int = Field(
        ...,
        example=42,
        description="ID of the user who owns this identity"
    )
    is_verified: bool = Field(
        ...,
        example=True,
        description="Whether this identity has been verified (required before use)"
    )
    is_complete: bool = Field(
        ...,
        example=True,
        description="Whether this identity has all required configuration (e.g., email configuration for EMAIL type)"
    )
    created_at: datetime = Field(
        ...,
        example="2023-03-10T09:00:00Z",
        description="When this identity was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        example="2023-03-15T14:30:00Z",
        description="When this identity was last updated"
    )

    model_config = ConfigDict(from_attributes=True)

class SenderIdentity(SenderIdentityInDBBase):
    """Complete sender identity model returned from API"""
    pass

class SenderIdentityWithConfig(SenderIdentity):
    """Sender identity with email configuration details (for EMAIL type)"""
    email_configuration_name: Optional[str] = Field(
        None,
        example="Company Gmail",
        description="Name of the associated email configuration (for EMAIL type)"
    )
    smtp_host: Optional[str] = Field(
        None,
        example="smtp.gmail.com",
        description="SMTP server from the associated configuration (for EMAIL type)"
    )
    email_from: Optional[str] = Field(
        None,
        example="notifications@yourcompany.com",
        description="From email address from the associated configuration (for EMAIL type)" 
    )