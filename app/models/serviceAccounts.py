from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ServiceAccount(Base):
    __tablename__ = "service_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_type = Column(Enum("EMAIL", "SMS", "WHATSAPP", name="service_type_enum"), nullable=False)
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
    
    # Add property methods for encrypted fields (similar to the Business model in your existing code)
    @property
    def smtp_password(self):
        # Decryption logic here
        pass
        
    @smtp_password.setter
    def smtp_password(self, value):
        # Encryption logic here
        pass
        
    # Similar properties for twilio_auth_token and whatsapp_api_key