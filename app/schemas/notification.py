from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.reminder import NotificationType, ReminderStatus


# Base Notification schema with shared properties
class NotificationBase(BaseModel):
    reminder_id: int
    recipient_id: int
    notification_type: NotificationType
    message: Optional[str] = None


# Schema for creating a notification
class NotificationCreate(NotificationBase):
    pass


# Schema for updating a notification
class NotificationUpdate(BaseModel):
    status: Optional[ReminderStatus] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Schema for notification in DB
class NotificationInDBBase(NotificationBase):
    id: int
    status: ReminderStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# Schema for returning notification data
class Notification(NotificationInDBBase):
    pass