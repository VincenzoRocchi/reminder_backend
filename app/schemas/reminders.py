from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class ReminderType(str, Enum):
    PAYMENT = "PAYMENT"
    DEADLINE = "DEADLINE"
    NOTIFICATION = "NOTIFICATION"

class NotificationType(str, Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"

class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reminder_type: ReminderType
    notification_type: NotificationType
    reminder_date: datetime
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_active: bool = True
    email_configuration_id: Optional[int] = None
    sender_identity_id: Optional[int] = None
    
    @field_validator('reminder_date')
    @classmethod
    def validate_reminder_date(cls, v: datetime) -> datetime:
        """
        Validate that the reminder date is in the future with a minimum buffer.
        
        A reminder must be scheduled at least 5 minutes in the future to allow
        for processing time and to prevent accidental immediate notifications.
        """
        min_buffer = timedelta(minutes=5)
        now = datetime.now()
        min_allowed_time = now + min_buffer
        
        if v < now:
            raise ValueError("Reminder date cannot be in the past")
        
        if v < min_allowed_time:
            raise ValueError(f"Reminder must be scheduled at least 5 minutes in the future (current minimum: {min_allowed_time.isoformat()})")
            
        return v

class ReminderCreate(ReminderBase):
    """Schema for creating a reminder"""
    client_ids: List[int]  # IDs of clients to receive the reminder

class ReminderCreateDB(ReminderBase):
    """Schema for creating a reminder in the database (without client_ids)"""
    user_id: int

class ReminderUpdate(BaseModel):
    """Schema for updating a reminder"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    reminder_type: Optional[ReminderType] = None
    notification_type: Optional[NotificationType] = None
    reminder_date: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    is_active: Optional[bool] = None
    email_configuration_id: Optional[int] = None
    client_ids: Optional[List[int]] = None  # IDs of clients to receive the reminder
    
    @field_validator('reminder_date')
    @classmethod
    def validate_reminder_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """
        Validate that the reminder date is in the future with a minimum buffer.
        Only validates if a new reminder_date is provided.
        """
        if v is None:
            return v
            
        min_buffer = timedelta(minutes=5)
        now = datetime.now()
        min_allowed_time = now + min_buffer
        
        if v < now:
            raise ValueError("Reminder date cannot be in the past")
        
        if v < min_allowed_time:
            raise ValueError(f"Reminder must be scheduled at least 5 minutes in the future (current minimum: {min_allowed_time.isoformat()})")
            
        return v

class ReminderInDBBase(ReminderBase):
    """Base schema for a reminder in database"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReminderSchema(ReminderInDBBase):
    """Complete reminder model returned from API"""
    pass

class ReminderDetail(ReminderSchema):
    """Reminder with client details"""
    clients: List[int]  # List of client IDs
    notifications_count: int = 0
    sent_count: int = 0
    failed_count: int = 0