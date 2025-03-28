from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.reminders import NotificationType, ReminderStatus

class NotificationBase(BaseModel):
    reminder_id: int = Field(
        ...,
        example=1,
        description="ID of the reminder this notification is for"
    )
    client_id: int = Field(
        ...,
        example=2,
        description="ID of the client receiving this notification"
    )
    notification_type: NotificationType = Field(
        ...,
        example="EMAIL",
        description="Method of delivery (EMAIL, SMS, WHATSAPP)"
    )
    message: Optional[str] = Field(
        None,
        example="Your invoice #INV-2023-42 is due in 3 days. Please process payment by June 30th.",
        description="Content of the notification message"
    )
    status: ReminderStatus = Field(
        ReminderStatus.PENDING,
        example="PENDING",
        description="Current status of the notification (PENDING, SENT, FAILED, CANCELLED)"
    )
    sender_identity_id: int = Field(
        ...,
        example=2,
        description="ID of the sender identity used for this notification"
    )

class NotificationCreate(NotificationBase):
    """Schema for creating a new notification"""
    pass

class NotificationCreateDB(NotificationBase):
    """Schema for storing a notification in the database (with user_id)"""
    user_id: int = Field(
        ...,
        example=42,
        description="ID of the user who owns this notification"
    )

class NotificationUpdate(BaseModel):
    """
    Schema for updating a notification's details
    
    Note: Status changes should be made through dedicated endpoints:
    - mark-as-sent
    - mark-as-failed
    - mark-as-cancelled
    """
    sent_at: Optional[datetime] = Field(
        None,
        example="2023-06-27T14:30:00Z",
        description="When the notification was sent"
    )
    error_message: Optional[str] = Field(
        None,
        example="Failed to deliver: recipient mailbox full",
        description="Error message if the notification failed to send"
    )
    sender_identity_id: Optional[int] = Field(
        None,
        example=3,
        description="Updated sender identity ID"
    )

class NotificationInDBBase(NotificationBase):
    """Base schema for a notification stored in the database with system fields"""
    id: int = Field(
        ...,
        example=1,
        description="Unique identifier for the notification"
    )
    user_id: int = Field(
        ...,
        example=42,
        description="ID of the user who owns this notification"
    )
    sent_at: Optional[datetime] = Field(
        None,
        example="2023-06-27T14:30:00Z",
        description="When the notification was sent"
    )
    error_message: Optional[str] = Field(
        None,
        example="Failed to deliver: recipient mailbox full",
        description="Error message if the notification failed to send"
    )
    created_at: datetime = Field(
        ...,
        example="2023-06-25T10:15:00Z",
        description="When the notification was created"
    )
    updated_at: Optional[datetime] = Field(
        None,
        example="2023-06-27T14:30:00Z",
        description="When the notification was last updated"
    )

    model_config = ConfigDict(from_attributes=True)

class NotificationSchema(NotificationInDBBase):
    """Complete notification model returned from API"""
    pass

class NotificationDetail(NotificationSchema):
    """Enhanced notification model with related entity details"""
    reminder_title: str = Field(
        ...,
        example="Quarterly Invoice Payment",
        description="Title of the reminder this notification is for"
    )
    client_name: str = Field(
        ...,
        example="Acme Corporation",
        description="Name of the client receiving this notification"
    )
    sender_identity_type: str = Field(
        ...,
        example="EMAIL",
        description="Type of the sender identity (EMAIL, PHONE, WHATSAPP)"
    )
    sender_identity_value: str = Field(
        ...,
        example="support@yourcompany.com",
        description="Email or phone number used to send this notification"
    )
    sender_identity_display_name: str = Field(
        ...,
        example="Company Support Team",
        description="Display name of the sender used for this notification"
    )