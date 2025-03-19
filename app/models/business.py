from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Business(Base):
    """
    Business database model
    """
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    email = Column(String(255))
    phone_number = Column(String(20))
    address = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Notification settings - Email
    smtp_host = Column(String(255))
    smtp_port = Column(Integer)
    smtp_user = Column(String(255))
    smtp_password = Column(String(255))
    email_from = Column(String(255))
    
    # Notification settings - SMS (Twilio)
    twilio_account_sid = Column(String(255))
    twilio_auth_token = Column(String(255))
    twilio_phone_number = Column(String(20))
    
    # Notification settings - WhatsApp
    whatsapp_api_key = Column(String(255))
    whatsapp_api_url = Column(String(255))

    # Relationships
    owner = relationship("User", back_populates="businesses")
    reminders = relationship("Reminder", back_populates="business", cascade="all, delete-orphan")