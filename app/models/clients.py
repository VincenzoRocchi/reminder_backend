from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import logging
import uuid
import re

from app.database import Base
from app.core.encryption import encryption_service
from app.core.exceptions import SensitiveDataStorageError, InvalidConfigurationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

class ContactMethodEnum(str, enum.Enum):
    """Enum for client contact method preferences"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    _phone_number = Column("phone_number", String(100), nullable=True)  # Encrypted
    address = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Enhanced contact information
    _secondary_phone_number = Column("secondary_phone_number", String(100), nullable=True)  # Encrypted
    _whatsapp_phone_number = Column("whatsapp_phone_number", String(100), nullable=True)  # Encrypted
    preferred_contact_method = Column(Enum(ContactMethodEnum), default=ContactMethodEnum.SMS)
    
    # Relationships
    user = relationship("User", back_populates="clients")
    reminder_recipients = relationship("ReminderRecipient", back_populates="client", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")
    
    # Phone number encryption and validation
    @property
    def phone_number(self) -> str:
        """Get decrypted phone number"""
        if not self._phone_number:
            return None
        try:
            return encryption_service.decrypt_string(self._phone_number)
        except Exception as e:
            logger.error(f"Decryption failed for phone number | Client ID:{self.id} | Error:{e}")
            return None

    @phone_number.setter
    def phone_number(self, value: str) -> None:
        """Set and encrypt phone number"""
        original_value = self._phone_number
        try:
            if value is None or value == "":
                self._phone_number = None
                return

            # Validate phone number format only if a non-empty value is provided
            if value and not re.match(r'^\+?[0-9]{10,15}$', value):
                logger.warning(f"Invalid phone number format | Client ID:{self.id}")
                raise InvalidConfigurationError("Client", "Phone number must be 10-15 digits, optionally starting with +")

            self._phone_number = encryption_service.encrypt_string(value)
            logger.info(f"Phone number updated | Client ID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._phone_number = original_value
            logger.error(f"Phone number storage failed | Client ID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("phone number") from e
            
    # Secondary phone number management
    @property
    def secondary_phone_number(self) -> str:
        """Get decrypted secondary phone number"""
        if not self._secondary_phone_number:
            return None
        try:
            return encryption_service.decrypt_string(self._secondary_phone_number)
        except Exception as e:
            logger.error(f"Decryption failed for secondary phone number | Client ID:{self.id} | Error:{e}")
            return None

    @secondary_phone_number.setter
    def secondary_phone_number(self, value: str) -> None:
        """Set and encrypt secondary phone number"""
        original_value = self._secondary_phone_number
        try:
            if value is None or value == "":
                self._secondary_phone_number = None
                return

            # Validate phone number format only if a non-empty value is provided
            if value and not re.match(r'^\+?[0-9]{10,15}$', value):
                logger.warning(f"Invalid secondary phone number format | Client ID:{self.id}")
                raise InvalidConfigurationError("Client", "Secondary phone number must be 10-15 digits, optionally starting with +")

            self._secondary_phone_number = encryption_service.encrypt_string(value)
            logger.info(f"Secondary phone number updated | Client ID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._secondary_phone_number = original_value
            logger.error(f"Secondary phone number storage failed | Client ID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("secondary phone number") from e
    
    # WhatsApp phone number management
    @property
    def whatsapp_phone_number(self) -> str:
        """Get decrypted WhatsApp phone number"""
        if not self._whatsapp_phone_number:
            return None
        try:
            return encryption_service.decrypt_string(self._whatsapp_phone_number)
        except Exception as e:
            logger.error(f"Decryption failed for WhatsApp phone number | Client ID:{self.id} | Error:{e}")
            return None

    @whatsapp_phone_number.setter
    def whatsapp_phone_number(self, value: str) -> None:
        """Set and encrypt WhatsApp phone number"""
        original_value = self._whatsapp_phone_number
        try:
            if value is None or value == "":
                self._whatsapp_phone_number = None
                return

            # Validate phone number format - WhatsApp requires "+" prefix if a non-empty value is provided
            if value and not re.match(r'^\+[0-9]{10,15}$', value):
                logger.warning(f"Invalid WhatsApp phone number format | Client ID:{self.id}")
                raise InvalidConfigurationError("Client", "WhatsApp phone number must be 10-15 digits with + prefix")

            self._whatsapp_phone_number = encryption_service.encrypt_string(value)
            logger.info(f"WhatsApp phone number updated | Client ID:{self.id}")

        except InvalidConfigurationError as ice:
            raise ice
        except Exception as e:
            self._whatsapp_phone_number = original_value
            logger.error(f"WhatsApp phone number storage failed | Client ID:{self.id} | TraceID:{uuid.uuid4()}")
            raise SensitiveDataStorageError("WhatsApp phone number") from e
    
    def __str__(self):
        return f"Client: {self.name} (User ID: {self.user_id})"
        
    def __repr__(self):
        return f"<Client id={self.id} name='{self.name}' user_id={self.user_id}>"