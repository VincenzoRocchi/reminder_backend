class Reminder(Base):
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reminder_type = Column(Enum("PAYMENT", "DEADLINE", "NOTIFICATION", name="reminder_type_enum"), nullable=False)
    notification_type = Column(Enum("EMAIL", "SMS", "WHATSAPP", name="notification_type_enum"), nullable=False)
    service_account_id = Column(Integer, ForeignKey("service_accounts.id"), nullable=True)
    
    # Schedule information
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(255), nullable=True)  # daily, weekly, monthly, etc.
    reminder_date = Column(DateTime(timezone=True), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    service_account = relationship("ServiceAccount", back_populates="reminders")
    reminder_recipients = relationship("ReminderRecipient", back_populates="reminder", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="reminder", cascade="all, delete-orphan")