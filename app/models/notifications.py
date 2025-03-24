class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    message = Column(Text, nullable=True)
    notification_type = Column(Enum("EMAIL", "SMS", "WHATSAPP", name="notification_type_enum"), nullable=False)
    status = Column(Enum("PENDING", "SENT", "FAILED", "CANCELLED", name="notification_status_enum"), default="PENDING")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    reminder = relationship("Reminder", back_populates="notifications")
    client = relationship("Client", back_populates="notifications")