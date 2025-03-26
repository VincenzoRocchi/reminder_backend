from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ReminderRecipientBase(BaseModel):
    reminder_id: int
    client_id: int

class ReminderRecipientCreate(ReminderRecipientBase):
    """Schema for creating a reminder recipient"""
    pass

class ReminderRecipientUpdate(BaseModel):
    """Schema for updating a reminder recipient"""
    reminder_id: Optional[int] = None
    client_id: Optional[int] = None

class ReminderRecipientInDBBase(ReminderRecipientBase):
    """Base schema for a reminder recipient in database"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ReminderRecipient(ReminderRecipientInDBBase):
    """Complete reminder recipient model returned from API"""
    pass

class ReminderRecipientDetail(ReminderRecipient):
    """Reminder recipient with extra details"""
    reminder_title: str
    client_name: str 