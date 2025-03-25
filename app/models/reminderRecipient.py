from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
import datetime
from sqlalchemy.orm import relationship

from app.database import Base

class ReminderRecipient(Base):
    __tablename__ = "reminder_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (UniqueConstraint('reminder_id', 'client_id', name='unique_reminder_client'),)
    
    # Relationships
    reminder = relationship("Reminder", back_populates="reminder_recipients")
    client = relationship("Client", back_populates="reminder_recipients")
    
    def __str__(self):
        return f"ReminderRecipient: Reminder {self.reminder_id} - Client {self.client_id}"
        
    def __repr__(self):
        return f"<ReminderRecipient reminder_id={self.reminder_id} client_id={self.client_id}>"