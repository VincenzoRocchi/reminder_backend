from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ReminderStatus(str, enum.Enum):
    """
    Enum for reminder status
    """
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    """
    Enum for notification types
    """
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class Reminder(Base):
    """
    Reminder database model
    """
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    reminder_date = Column(DateTime(timezone=True), nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(255))
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    business = relationship("Business", back_populates="reminders")
    creator = relationship("User", foreign_keys=[created_by])
    notifications = relationship("Notification", back_populates="reminder", cascade="all, delete-orphan")
    
    def __str__(self):
        status = "active" if getattr(self, "is_active", False) else "inactive"
        return f"Reminder: {self.title} ({status}) - {self.reminder_date.strftime('%Y-%m-%d %H:%M')}"

    def __repr__(self):
        recurrence = f", recurs: {self.recurrence_pattern}" if getattr(self, "is_recurring", False) else ""
        return f"<Reminder id={self.id} title='{self.title}' date='{self.reminder_date}' type={self.notification_type}{recurrence} active={self.is_active}>"