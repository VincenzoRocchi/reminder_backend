from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

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
    phone_number = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Enhanced contact information
    secondary_phone_number = Column(String(20), nullable=True)
    whatsapp_phone_number = Column(String(20), nullable=True)
    preferred_contact_method = Column(Enum(ContactMethodEnum), default=ContactMethodEnum.SMS)
    
    # Relationships
    user = relationship("User", back_populates="clients")
    reminder_recipients = relationship("ReminderRecipient", back_populates="client", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")
    
    def __str__(self):
        return f"Client: {self.name} (User ID: {self.user_id})"
        
    def __repr__(self):
        return f"<Client id={self.id} name='{self.name}' user_id={self.user_id}>"