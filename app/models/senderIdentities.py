from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class IdentityTypeEnum(str, enum.Enum):
    """Enum for sender identity types"""
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"  # Added WhatsApp as a distinct type

class SenderIdentity(Base):
    __tablename__ = "sender_identities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    identity_type = Column(Enum(IdentityTypeEnum), nullable=False)
    
    # New split fields instead of a single 'value' field
    email = Column(String(255), nullable=True)  # Required if identity_type is EMAIL
    phone_number = Column(String(20), nullable=True)  # Required if identity_type is PHONE or WHATSAPP
    
    # Remove the value field
    # value = Column(String(255), nullable=False)  # Phone number or email
    
    display_name = Column(String(255), nullable=False)  # How it appears to recipients
    is_verified = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Link to email configuration for EMAIL type identities
    email_configuration_id = Column(Integer, ForeignKey("email_configurations.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sender_identities")
    reminders = relationship("Reminder", back_populates="sender_identity")
    email_configuration = relationship("EmailConfiguration")
    notifications = relationship("Notification", back_populates="sender_identity")
    
    def __str__(self):
        if self.identity_type == IdentityTypeEnum.EMAIL:
            return f"SenderIdentity: {self.display_name} ({self.email})"
        else:
            return f"SenderIdentity: {self.display_name} ({self.phone_number})"
        
    def __repr__(self):
        if self.identity_type == IdentityTypeEnum.EMAIL:
            return f"<SenderIdentity id={self.id} type={self.identity_type} email='{self.email}'>"
        else:
            return f"<SenderIdentity id={self.id} type={self.identity_type} phone='{self.phone_number}'>"