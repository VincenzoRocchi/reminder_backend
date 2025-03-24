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