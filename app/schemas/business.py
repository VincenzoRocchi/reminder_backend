from pydantic import BaseModel, EmailStr, Field, model_validator, field_serializer, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.encryption import encryption_service


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
    
    # Define which fields should be encrypted
    _sensitive_fields = ['smtp_password', 'twilio_auth_token', 'whatsapp_api_key']
    
    model_config = ConfigDict(
        from_attributes=True,  # Modern replacement for orm_mode=True
    )
    
    # This validator runs when creating the model from dict or ORM object
    @model_validator(mode='before')
    @classmethod
    def decrypt_sensitive_data(cls, data: Any) -> Dict[str, Any]:
        # If data is an ORM object, extract all fields
        if hasattr(data, '__dict__'):
            # Start with the __dict__
            data_dict = {**data.__dict__}
            
            # If it has __fields__ (like a Pydantic v1 model), get all fields
            if hasattr(data, '__fields__'):
                for field in data.__fields__:
                    if hasattr(data, field):
                        data_dict[field] = getattr(data, field)
        else:
            # Already a dictionary
            data_dict = dict(data)
        
        # Decrypt sensitive fields
        for field in cls._sensitive_fields:
            if field in data_dict and data_dict[field]:
                try:
                    data_dict[field] = encryption_service.decrypt_string(data_dict[field])
                except Exception as e:
                    # If decryption fails, keep original value
                    pass
        
        return data_dict
    
    # Field serializers for encryption when serializing to dict
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


# Schema for returning business data
class Business(BusinessInDBBase):
    pass