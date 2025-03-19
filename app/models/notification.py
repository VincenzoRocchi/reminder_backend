from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.reminder import ReminderStatus, NotificationType


class Notification(Base):
    """
    Notification database model
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ReminderStatus), default=ReminderStatus.PENDING)
    notification_type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text)
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    reminder = relationship("Reminder", back_populates="notifications")
    recipient = relationship("User", foreign_keys=[recipient_id])