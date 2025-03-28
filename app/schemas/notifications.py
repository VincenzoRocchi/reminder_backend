from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.reminders import NotificationType, ReminderStatus

class NotificationBase(BaseModel):
    reminder_id: int
    client_id: int
    notification_type: NotificationType
    message: Optional[str] = None
    status: ReminderStatus = ReminderStatus.PENDING

class NotificationCreate(NotificationBase):
    """Schema for creating a notification"""
    pass

class NotificationCreateDB(NotificationBase):
    """Schema for creating a notification in the database (with user_id)"""
    user_id: int

class NotificationUpdate(BaseModel):
    """
    Schema for updating a notification
    
    Note: Status changes should be made through dedicated endpoints:
    - mark-as-sent
    - mark-as-failed
    - mark-as-cancelled
    """
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None

class NotificationInDBBase(NotificationBase):
    """Base schema for a notification in database"""
    id: int
    user_id: int
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class NotificationSchema(NotificationInDBBase):
    """Complete notification model returned from API"""
    pass

class NotificationDetail(NotificationSchema):
    """Notification with extra details"""
    reminder_title: str
    client_name: str