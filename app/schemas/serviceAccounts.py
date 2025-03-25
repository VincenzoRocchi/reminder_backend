from pydantic import BaseModel, Field, EmailStr, model_validator, field_serializer, ConfigDict
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime
from enum import Enum
from app.core.encryption import encryption_service
from app.core.validators import (
    flexible_field_validator,
    validate_twilio_token,
    validate_smtp_password,
    validate_whatsapp_api_key
)

class ServiceType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class ServiceAccountBase(BaseModel):
    service_type: ServiceType
    service_name: str = Field(..., min_length=2, max_length=255)
    is_active: bool = True
    
    # Email settings - only required if service_type is EMAIL
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # SMS settings - only required if service_type is SMS
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # WhatsApp settings - only required if service_type is WHATSAPP
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None
    
    # Validation
    _validate_smtp_password = flexible_field_validator('smtp_password', 'format')(validate_smtp_password)
    _validate_twilio_token = flexible_field_validator('twilio_auth_token', 'format')(validate_twilio_token)
    _validate_whatsapp_key = flexible_field_validator('whatsapp_api_key', 'format')(validate_whatsapp_api_key)
    
    @model_validator(mode='after')
    def validate_service_config(self) -> 'ServiceAccountBase':
        """Validate service configuration based on service type"""
        if self.service_type == ServiceType.EMAIL:
            # For email service, SMTP credentials are required
            if any([self.smtp_host, self.smtp_user, self.smtp_password]) and not all([self.smtp_host, self.smtp_port, self.smtp_user]):
                raise ValueError("Email service requires smtp_host, smtp_port, and smtp_user")
        elif self.service_type == ServiceType.SMS:
            # For SMS service, Twilio credentials are required
            if any([self.twilio_account_sid, self.twilio_auth_token]) and not all([self.twilio_account_sid, self.twilio_phone_number]):
                raise ValueError("SMS service requires twilio_account_sid and twilio_phone_number")
        elif self.service_type == ServiceType.WHATSAPP:
            # For WhatsApp service, WhatsApp API credentials are required
            if any([self.whatsapp_api_key, self.whatsapp_api_url]) and not all([self.whatsapp_api_key, self.whatsapp_api_url, self.whatsapp_phone_number]):
                raise ValueError("WhatsApp service requires whatsapp_api_key, whatsapp_api_url, and whatsapp_phone_number")
        return self

class ServiceAccountCreate(ServiceAccountBase):
    """Schema for creating a service account"""
    pass

class ServiceAccountUpdate(BaseModel):
    """Schema for updating a service account"""
    service_name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
    
    # Email settings
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    # SMS settings
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # WhatsApp settings
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None
    
    # Validation
    _validate_smtp_password = flexible_field_validator('smtp_password', 'format')(validate_smtp_password)
    _validate_twilio_token = flexible_field_validator('twilio_auth_token', 'format')(validate_twilio_token)
    _validate_whatsapp_key = flexible_field_validator('whatsapp_api_key', 'format')(validate_whatsapp_api_key)

class ServiceAccountInDBBase(ServiceAccountBase):
    """Base schema for a service account in database"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # List of fields that should be encrypted/decrypted
    _sensitive_fields: ClassVar[list[str]] = ['smtp_password', 'twilio_auth_token', 'whatsapp_api_key']
    
    model_config = ConfigDict(
        from_attributes=True,
    )
    
    @model_validator(mode='before')
    @classmethod
    def decrypt_sensitive_data(cls, data: Any) -> Dict[str, Any]:
        """Decrypt sensitive data from the database"""
        data_dict = dict(data.__dict__) if hasattr(data, '__dict__') else dict(data)

        for field in cls._sensitive_fields:
            if field in data_dict and data_dict[field]:
                try:
                    data_dict[field] = encryption_service.decrypt_string(data_dict[field])
                except Exception:
                    pass

        return data_dict
    
    @field_serializer('smtp_password')
    def encrypt_smtp_password(self, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return encryption_service.encrypt_string(v)
        return v
    
    @field_serializer('twilio_auth_token')
    def encrypt_twilio_auth_token(self, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return encryption_service.encrypt_string(v)
        return v
    
    @field_serializer('whatsapp_api_key')
    def encrypt_whatsapp_api_key(self, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return encryption_service.encrypt_string(v)
        return v

class ServiceAccount(ServiceAccountInDBBase):
    """Complete service account model returned from API"""
    pass