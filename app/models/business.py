# Update app/models/business.py to store encrypted credentials
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import Optional
from datetime import datetime

from app.database import Base
from app.core.encryption import encryption_service


class Business(Base):
    """
    Business database model with encrypted sensitive fields
    
    This model handles encryption and decryption of sensitive data transparently
    using Python properties. The actual encrypted values are stored in columns
    prefixed with an underscore, while clean accessor properties provide
    automatic encryption/decryption.
    """
    __tablename__ = "businesses"
    
    # Regular fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(String(500))
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    
    # Email notification settings
    smtp_host: Mapped[Optional[str]] = mapped_column(String(255))
    smtp_port: Mapped[Optional[int]] = mapped_column(Integer)
    smtp_user: Mapped[Optional[str]] = mapped_column(String(255))
    _smtp_password: Mapped[Optional[str]] = mapped_column("smtp_password", String(500))  # Encrypted field
    email_from: Mapped[Optional[str]] = mapped_column(String(255))
    
    # SMS notification settings
    twilio_account_sid: Mapped[Optional[str]] = mapped_column(String(255))
    _twilio_auth_token: Mapped[Optional[str]] = mapped_column("twilio_auth_token", String(500))  # Encrypted field
    twilio_phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    
    # WhatsApp notification settings
    _whatsapp_api_key: Mapped[Optional[str]] = mapped_column("whatsapp_api_key", String(500))  # Encrypted field
    whatsapp_api_url: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Relationships
    owner = relationship("User", back_populates="businesses")
    reminders = relationship("Reminder", back_populates="business", cascade="all, delete-orphan")
    
    # Properties for encrypted fields with improved error handling and logging
    @property
    def smtp_password(self) -> Optional[str]:
        """
        Get decrypted SMTP password
        
        Returns:
            Decrypted password or None if not set or decryption fails
        """
        if not self._smtp_password:
            return None
        
        try:
            return encryption_service.decrypt_string(self._smtp_password)
        except Exception as e:
            # Log the error but preserve privacy by not logging the actual encrypted value
            import logging
            logging.error(f"Failed to decrypt smtp_password for business {self.id}: {str(e)}")
            return None
    
    @smtp_password.setter
    def smtp_password(self, value: Optional[str]) -> None:
        """
        Set SMTP password, encrypting it before storage
        
        Args:
            value: Plain text password to encrypt and store
        """
        if value is None:
            self._smtp_password = None
        else:
            try:
                self._smtp_password = encryption_service.encrypt_string(str(value))
            except Exception as e:
                import logging
                logging.error(f"Failed to encrypt smtp_password for business {self.id}: {str(e)}")
                # Avoid storing unencrypted sensitive data in case of encryption failure
                self._smtp_password = None
                # Raise exception to prevent silent security failures
                raise ValueError("Failed to encrypt sensitive data") from e
    
    @property
    def twilio_auth_token(self) -> Optional[str]:
        """
        Get decrypted Twilio auth token
        
        Returns:
            Decrypted token or None if not set or decryption fails
        """
        if not self._twilio_auth_token:
            return None
        
        try:
            return encryption_service.decrypt_string(self._twilio_auth_token)
        except Exception as e:
            import logging
            logging.error(f"Failed to decrypt twilio_auth_token for business {self.id}: {str(e)}")
            return None
    
    @twilio_auth_token.setter
    def twilio_auth_token(self, value: Optional[str]) -> None:
        """
        Set Twilio auth token, encrypting it before storage
        
        Args:
            value: Plain text token to encrypt and store
        """
        if value is None:
            self._twilio_auth_token = None
        else:
            try:
                self._twilio_auth_token = encryption_service.encrypt_string(str(value))
            except Exception as e:
                import logging
                logging.error(f"Failed to encrypt twilio_auth_token for business {self.id}: {str(e)}")
                self._twilio_auth_token = None
                raise ValueError("Failed to encrypt sensitive data") from e
    
    @property
    def whatsapp_api_key(self) -> Optional[str]:
        """
        Get decrypted WhatsApp API key
        
        Returns:
            Decrypted API key or None if not set or decryption fails
        """
        if not self._whatsapp_api_key:
            return None
        
        try:
            return encryption_service.decrypt_string(self._whatsapp_api_key)
        except Exception as e:
            import logging
            logging.error(f"Failed to decrypt whatsapp_api_key for business {self.id}: {str(e)}")
            return None
    
    @whatsapp_api_key.setter
    def whatsapp_api_key(self, value: Optional[str]) -> None:
        """
        Set WhatsApp API key, encrypting it before storage
        
        Args:
            value: Plain text API key to encrypt and store
        """
        if value is None:
            self._whatsapp_api_key = None
        else:
            try:
                self._whatsapp_api_key = encryption_service.encrypt_string(str(value))
            except Exception as e:
                import logging
                logging.error(f"Failed to encrypt whatsapp_api_key for business {self.id}: {str(e)}")
                self._whatsapp_api_key = None
                raise ValueError("Failed to encrypt sensitive data") from e