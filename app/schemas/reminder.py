from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enum for notification types
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


# Enum for reminder status
class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Base Reminder schema with shared properties
class ReminderBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    reminder_date: datetime
    notification_type: NotificationType
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_active: bool = True


# Schema for creating a reminder
class ReminderCreate(ReminderBase):
    business_id: int
    recipient_ids: List[int]  # IDs of users to receive the reminder


# Schema for updating a reminder
class ReminderUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    reminder_date: Optional[datetime] = None
    notification_type: Optional[NotificationType] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    is_active: Optional[bool] = None
    recipient_ids: Optional[List[int]] = None


# Schema for reminder in DB
class ReminderInDBBase(ReminderBase):
    id: int
    business_id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Schema for returning reminder data
class Reminder(ReminderInDBBase):
    pass


# Detailed reminder with recipients
class ReminderDetail(Reminder):
    recipients: List[int]  # List of recipient IDs