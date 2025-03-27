from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base

class ReminderTypeEnum(str, enum.Enum):
    """Enum for reminder types"""
    PAYMENT = "PAYMENT"
    DEADLINE = "DEADLINE"
    NOTIFICATION = "NOTIFICATION"

class NotificationTypeEnum(str, enum.Enum):
    """Enum for notification types"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reminder_type = Column(Enum(ReminderTypeEnum), nullable=False)
    notification_type = Column(Enum(NotificationTypeEnum), nullable=False)
    email_configuration_id = Column(Integer, ForeignKey("email_configurations.id"), nullable=True)
    sender_identity_id = Column(Integer, ForeignKey("sender_identities.id"), nullable=True)
    
    # Schedule information
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(255), nullable=True)  # daily, weekly, monthly, etc.
    reminder_date = Column(DateTime(timezone=True), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    email_configuration = relationship("EmailConfiguration", back_populates="reminders")
    reminder_recipients = relationship("ReminderRecipient", back_populates="reminder", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="reminder", cascade="all, delete-orphan")
    sender_identity = relationship("SenderIdentity", back_populates="reminders")
    
    def __str__(self):
        return f"Reminder: {self.title} ({self.reminder_date})"
        
    def __repr__(self):
        return f"<Reminder id={self.id} title='{self.title}' type={self.reminder_type} date={self.reminder_date}>"