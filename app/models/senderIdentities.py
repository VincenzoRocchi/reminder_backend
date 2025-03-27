from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class IdentityTypeEnum(str, enum.Enum):
    """Enum for sender identity types"""
    PHONE = "PHONE"
    EMAIL = "EMAIL"

class SenderIdentity(Base):
    __tablename__ = "sender_identities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    identity_type = Column(Enum(IdentityTypeEnum), nullable=False)
    value = Column(String(255), nullable=False)  # Phone number or email
    display_name = Column(String(255), nullable=False)  # How it appears to recipients
    is_verified = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sender_identities")
    reminders = relationship("Reminder", back_populates="sender_identity")
    
    def __str__(self):
        return f"SenderIdentity: {self.display_name} ({self.value})"
        
    def __repr__(self):
        return f"<SenderIdentity id={self.id} type={self.identity_type} value='{self.value}'>"