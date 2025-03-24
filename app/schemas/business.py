# --------------------------------PRODUCTION NOTES--------------------------------
#
# 1. VALIDATIONS
#    - Validators (SMTP, Twilio, WhatsApp) ensure sensitive data meets required formats
#    - Consider enabling STRICT_VALIDATION in production for:
#      --Stronger data validation
#      --Prevention of misconfiguration
#      --Enhanced security checks
#
# 2. SENSITIVE DATA SERIALIZATION
#    - BusinessInDBBase handles decryption of sensitive fields
#    - Production Security Checklist:
#      --Verify encryption key management
#      --Monitor decryption processes
#      --Ensure no unencrypted data exposure
#      --Implement proper key rotation
#
# 3. MODULARITY
#    - Use these schemas as templates for new implementations
#    - Maintain consistent structure across the application
#    - Follow established patterns for:
#      --Field validation
#      --Data encryption
#      --Error handling
# -----------------------------------------------------------------------------

from pydantic import BaseModel, EmailStr, Field, model_validator, field_serializer, ConfigDict
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime
from app.core.encryption import encryption_service
from app.core.validators import (
    flexible_field_validator,
    validate_twilio_token,
    validate_smtp_password,
    validate_whatsapp_api_key
)


class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = True
    
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
    
    # Flexible validators
    _validate_smtp_password = flexible_field_validator('smtp_password', 'format')(validate_smtp_password)
    _validate_twilio_token = flexible_field_validator('twilio_auth_token', 'format')(validate_twilio_token)
    _validate_whatsapp_key = flexible_field_validator('whatsapp_api_key', 'format')(validate_whatsapp_api_key)


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None
    
    _validate_smtp_password = flexible_field_validator('smtp_password', 'format')(validate_smtp_password)
    _validate_twilio_token = flexible_field_validator('twilio_auth_token', 'format')(validate_twilio_token)
    _validate_whatsapp_key = flexible_field_validator('whatsapp_api_key', 'format')(validate_whatsapp_api_key)


class BusinessNotificationSettings(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    whatsapp_api_key: Optional[str] = None
    whatsapp_api_url: Optional[str] = None
    
    _validate_smtp_password = flexible_field_validator('smtp_password', 'format')(validate_smtp_password)
    _validate_twilio_token = flexible_field_validator('twilio_auth_token', 'format')(validate_twilio_token)
    _validate_whatsapp_key = flexible_field_validator('whatsapp_api_key', 'format')(validate_whatsapp_api_key)


class BusinessInDBBase(BusinessBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # soluzione definitiva, robusta, ufficiale e corretta - lista costante e non campo-Pydantic - raccomandato anche per produzione
    _sensitive_fields: ClassVar[list[str]] = ['smtp_password', 'twilio_auth_token', 'whatsapp_api_key']
    
    model_config = ConfigDict(
        from_attributes=True,
    )
    
    @model_validator(mode='before')
    @classmethod
    def decrypt_sensitive_data(cls, data: Any) -> Dict[str, Any]:
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


class Business(BusinessInDBBase):
    pass