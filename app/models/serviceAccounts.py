# app/models/serviceAccounts.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from typing import Optional
import logging
import uuid
import enum

from app.database import Base
from app.core.encryption import encryption_service
from app.core.exceptions import SensitiveDataStorageError, InvalidConfigurationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

class ServiceTypeEnum(str, enum.Enum):
    """Enum for service types"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    
    # Basic fields
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(Enum(ServiceTypeEnum), nullable=False)
    service_name = Column(String(255), nullable=False)  # User-friendly name for the service
    
    # Email service credentials
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_user = Column(String(255), nullable=True)
    _smtp_password = Column("smtp_password", String(500), nullable=True)  # Encrypted
    email_from = Column(String(255), nullable=True)
    
    # SMS service credentials (Twilio)
    twilio_account_sid = Column(String(255), nullable=True)
    _twilio_auth_token = Column("twilio_auth_token", String(500), nullable=True)  # Encrypted
    twilio_phone_number = Column(String(20), nullable=True)
    
    # WhatsApp service credentials
    _whatsapp_api_key = Column("whatsapp_api_key", String(500), nullable=True)  # Encrypted
    whatsapp_api_url = Column(String(255), nullable=True)
    whatsapp_phone_number = Column(String(20), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="service_accounts")
    reminders = relationship("Reminder", back_populates="service_account")
    
    # SMTP Password management
    @property
    def smtp_password(self) -> Optional[str]:
        """Get decrypted SMTP password or try secrets"""
        if not self._smtp_password:
            # Try to get from secrets
            try:
                from app.core.secrets_manager import secrets_manager
                email_secrets = secrets_manager.get_category("email")
                if email_secrets and "smtp_password" in email_secrets:
                    return email_secrets["smtp_password"]
            except Exception:
                pass
            return None
        
        try:
            return encryption_service.decrypt_string(self._smtp_password)
        except Exception as e:
            logger.error(f"Decryption failed for SMTP password | ServiceID:{self.id} | Error:{e}")
            return None

    @smtp_password.setter
    def smtp_password(self, value: Optional[str]) -> None:
        """Set and encrypt SMTP password"""
        original_value = self._smtp_password
        try:
            if value is None:
                self._smtp_password = None
                return

            # Only enforce length requirement if strict validation is enabled
            if settings.should_validate('format') and len(value) < 8:
                logger.warning(f"SMTP password too short | ServiceID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                
                if settings.STRICT_VALIDATION:
                    raise InvalidConfigurationError("SMTP", "Password must be at least 8 characters")
                # If not strict, continue despite validation failure

            self._smtp_password = encryption_service.encrypt_string(value)
            logger.info(f"SMTP password updated | ServiceID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._smtp_password = original_value
            logger.error(f"SMTP password storage failed | ServiceID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("SMTP password") from e

    # Twilio Auth Token management
    @property
    def twilio_auth_token(self) -> Optional[str]:
        """Get decrypted Twilio auth token or try secrets"""
        if not self._twilio_auth_token:
            # Try to get from secrets
            try:
                from app.core.secrets_manager import secrets_manager
                sms_secrets = secrets_manager.get_category("sms")
                if sms_secrets and "twilio_auth_token" in sms_secrets:
                    return sms_secrets["twilio_auth_token"]
            except Exception:
                pass
            return None
        
        try:
            return encryption_service.decrypt_string(self._twilio_auth_token)
        except Exception as e:
            logger.error(f"Decryption failed for Twilio token | ServiceID:{self.id} | Error:{e}")
            return None

    @twilio_auth_token.setter
    def twilio_auth_token(self, value: Optional[str]) -> None:
        """Set and encrypt Twilio auth token with validation"""
        original_value = self._twilio_auth_token
        try:
            if value is None:
                self._twilio_auth_token = None
                return

            # Only validate format if strict validation is enabled
            if settings.should_validate('format'):
                if len(value) != 32 or not value.startswith('SK'):
                    # Log the validation issue even if we bypass
                    logger.warning(f"Twilio token format invalid | ServiceID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                    
                    if settings.STRICT_VALIDATION:
                        raise InvalidConfigurationError(
                            "Twilio", 
                            "Auth token must be 32 characters starting with 'SK'"
                        )
                    # If not strict, continue despite validation failure
            
            # Always encrypt, even if validation is bypassed
            self._twilio_auth_token = encryption_service.encrypt_string(value)
            logger.info(f"Twilio token updated | ServiceID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._twilio_auth_token = original_value
            logger.error(f"Twilio token storage failed | ServiceID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("Twilio auth token") from e

    # WhatsApp API Key management
    @property
    def whatsapp_api_key(self) -> Optional[str]:
        """Get decrypted WhatsApp API key or try secrets"""
        if not self._whatsapp_api_key:
            # Try to get from secrets
            try:
                from app.core.secrets_manager import secrets_manager
                whatsapp_secrets = secrets_manager.get_category("whatsapp")
                if whatsapp_secrets and "api_key" in whatsapp_secrets:
                    return whatsapp_secrets["api_key"]
            except Exception:
                pass
            return None
        
        try:
            return encryption_service.decrypt_string(self._whatsapp_api_key)
        except Exception as e:
            logger.error(f"Decryption failed for WhatsApp API key | ServiceID:{self.id} | Error:{e}")
            return None

    @whatsapp_api_key.setter
    def whatsapp_api_key(self, value: Optional[str]) -> None:
        """Set and encrypt WhatsApp API key"""
        original_value = self._whatsapp_api_key
        try:
            if value is None:
                self._whatsapp_api_key = None
                return

            # Only enforce length requirement if strict validation is enabled
            if settings.should_validate('format') and len(value) < 16:
                logger.warning(f"WhatsApp API key too short | ServiceID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                
                if settings.STRICT_VALIDATION:
                    raise InvalidConfigurationError("WhatsApp", "API key must be at least 16 characters")
                # If not strict, continue despite validation failure

            self._whatsapp_api_key = encryption_service.encrypt_string(value)
            logger.info(f"WhatsApp API key updated | ServiceID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._whatsapp_api_key = original_value
            logger.error(f"WhatsApp key storage failed | ServiceID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("WhatsApp API key") from e
            
    def __str__(self):
        return f"ServiceAccount: {self.service_name} ({self.service_type})"

    def __repr__(self):
        return f"<ServiceAccount id={self.id} type={self.service_type} user_id={self.user_id} active={self.is_active}>"