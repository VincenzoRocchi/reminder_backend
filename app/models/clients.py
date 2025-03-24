from sqlalchemy import Column, Integer, String, Date
from app.database import Base

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
    
    # Relationships
    user = relationship("User", back_populates="clients")
    reminder_recipients = relationship("ReminderRecipient", back_populates="client", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="client", cascade="all, delete-orphan")