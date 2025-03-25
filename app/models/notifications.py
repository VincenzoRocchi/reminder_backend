from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
import datetime

from app.database import Base

class NotificationStatusEnum(str, enum.Enum):
    """Enum for notification status"""
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    message = Column(Text, nullable=True)
    notification_type = Column(Enum("EMAIL", "SMS", "WHATSAPP", name="notification_type_enum"), nullable=False)
    status = Column(Enum(NotificationStatusEnum), default=NotificationStatusEnum.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    reminder = relationship("Reminder", back_populates="notifications")
    client = relationship("Client", back_populates="notifications")
    
    def __str__(self):
        return f"Notification: {self.notification_type} for Client {self.client_id} ({self.status})"
        
    def __repr__(self):
        sent_time = self.sent_at.strftime('%Y-%m-%d %H:%M') if self.sent_at else "Not sent"
        return f"<Notification id={self.id} type={self.notification_type} client={self.client_id} status={self.status} sent={sent_time}>"