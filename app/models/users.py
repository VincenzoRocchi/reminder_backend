from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import logging
import uuid
import re

from app.database import Base
from app.core.encryption import encryption_service
from app.core.exceptions import SensitiveDataStorageError, InvalidConfigurationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

class User(Base):
    __tablename__ = "users"
    
    # Basic user information
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    business_name = Column(String(255), nullable=True)  # Optional for business users
    _phone_number = Column("phone_number", String(20), nullable=True)  # Encrypted
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Usage tracking for billing
    sms_count = Column(Integer, default=0)
    whatsapp_count = Column(Integer, default=0)
    last_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    email_configurations = relationship("EmailConfiguration", back_populates="user", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    sender_identities = relationship("SenderIdentity", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
    # Phone number encryption (using the same pattern as in Business model)
    @property
    def phone_number(self) -> str:
        """Get decrypted phone number"""
        try:
            if not self._phone_number:
                return None
            return encryption_service.decrypt_string(self._phone_number)
        except Exception as e:
            # If decryption fails, log but don't break authentication by raising exceptions
            logger.error(f"Decryption failed for phone number | User ID:{self.id} | Error:{e}")
            return None

    @phone_number.setter
    def phone_number(self, value: str) -> None:
        """Set and encrypt phone number"""
        try:
            # Clear the value if None or empty
            if value is None or value == "":
                self._phone_number = None
                return

            # Validate phone number format only if a value is provided
            if value and not re.match(r'^\+?[0-9]{10,15}$', value):
                logger.warning(f"Invalid phone number format | User ID:{self.id}")
                # Don't raise exceptions during object initialization that could block authentication
                # Just log the warning and proceed with encryption
                
            # Always encrypt even if validation fails to prevent authentication issues
            self._phone_number = encryption_service.encrypt_string(value)
            logger.info(f"Phone number updated | User ID:{self.id}")

        except Exception as e:
            # Don't let encryption errors break the main app flow
            self._phone_number = None  # Set to None on error instead of keeping original
            logger.error(f"Phone number storage failed | User ID:{self.id} | TraceID:{uuid.uuid4()}")
            # Don't raise exception that could break authentication
            
    def __str__(self):
        return f"User: {self.username} ({self.email})"

    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' email='{self.email}' active={self.is_active}>"