from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import logging
import uuid

from app.database import Base
from app.core.encryption import encryption_service
from app.core.exceptions import SensitiveDataStorageError, InvalidConfigurationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

class EmailConfiguration(Base):
    __tablename__ = "email_configurations"
    
    # Basic fields
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    configuration_name = Column(String(255), nullable=False)  # "Company Newsletter", "Support Team", etc.
    
    # Email service credentials
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_user = Column(String(255), nullable=False)
    _smtp_password = Column("smtp_password", String(500), nullable=False)  # Encrypted
    email_from = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="email_configurations")
    reminders = relationship("Reminder", back_populates="email_configuration")
    
    # SMTP Password management
    @property
    def smtp_password(self) -> str:
        """Get decrypted SMTP password"""
        if not self._smtp_password:
            return None
        
        try:
            return encryption_service.decrypt_string(self._smtp_password)
        except Exception as e:
            logger.error(f"Decryption failed for SMTP password | ConfigID:{self.id} | Error:{e}")
            return None

    @smtp_password.setter
    def smtp_password(self, value: str) -> None:
        """Set and encrypt SMTP password"""
        original_value = self._smtp_password
        try:
            if value is None:
                self._smtp_password = None
                return

            # Only enforce length requirement if strict validation is enabled
            if settings.should_validate('format') and len(value) < 8:
                logger.warning(f"SMTP password too short | ConfigID:{self.id} | STRICT_VALIDATION: {settings.STRICT_VALIDATION}")
                
                if settings.STRICT_VALIDATION:
                    raise InvalidConfigurationError("SMTP", "Password must be at least 8 characters")
                # If not strict, continue despite validation failure

            self._smtp_password = encryption_service.encrypt_string(value)
            logger.info(f"SMTP password updated | ConfigID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._smtp_password = original_value
            logger.error(f"SMTP password storage failed | ConfigID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("SMTP password") from e
            
    def __str__(self):
        return f"EmailConfiguration: {self.configuration_name} ({self.email_from})"

    def __repr__(self):
        return f"<EmailConfiguration id={self.id} name='{self.configuration_name}' user_id={self.user_id} active={self.is_active}>"