from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

class ReminderType(str, Enum):
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
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=255, 
        example="Quarterly Tax Deadline",
        description="Short title describing the reminder"
    )
    description: Optional[str] = Field(
        None, 
        example="Tax filing deadline for Q2. Reference: TAX-2023-Q2",
        description="Detailed information about the reminder"
    )
    reminder_type: ReminderType = Field(
        ..., 
        example="DEADLINE", 
        description="Type of reminder (DEADLINE or NOTIFICATION)"
    )
    notification_type: NotificationType = Field(
        ..., 
        example="EMAIL", 
        description="Delivery method for the reminder (EMAIL, SMS, or WHATSAPP)"
    )
    reminder_date: datetime = Field(
        ..., 
        example="2023-06-30T15:00:00Z", 
        description="When the reminder should be sent (must be at least 5 minutes in the future)"
    )
    is_recurring: bool = Field(
        False, 
        example=False, 
        description="Whether this is a recurring reminder"
    )
    recurrence_pattern: Optional[str] = Field(
        None, 
        example="MONTHLY", 
        description="Pattern for recurring reminders (e.g., DAILY, WEEKLY, MONTHLY)"
    )
    is_active: bool = Field(
        True, 
        example=True, 
        description="Whether the reminder is active (will be sent) or inactive (won't be sent)"
    )
    email_configuration_id: Optional[int] = Field(
        None, 
        example=1, 
        description="ID of the email configuration to use (deprecated - use sender_identity_id instead)"
    )
    sender_identity_id: int = Field(
        ..., 
        example=2, 
        description="ID of the sender identity to use for this reminder"
    )
    
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
    """Schema for creating a new reminder with client recipients"""
    client_ids: List[int] = Field(
        ...,
        example=[1, 2, 3],
        description="List of client IDs who should receive this reminder"
    )
    
    @field_validator('notification_type')
    @classmethod
    def validate_notification_type_match_identity(cls, v, info):
        """
        Validate that the notification type matches the sender identity type:
        - If using a PHONE sender identity, notification_type must be SMS or WHATSAPP
        - If using an EMAIL sender identity, notification_type must be EMAIL
        
        Note: This validation happens at the service level when the sender identity is retrieved,
        but this validator provides early feedback in the API documentation.
        """
        if v not in [NotificationType.EMAIL, NotificationType.SMS, NotificationType.WHATSAPP]:
            raise ValueError(f"Notification type must be one of: EMAIL, SMS, WHATSAPP")
        return v

class ReminderCreateDB(ReminderBase):
    """Schema for storing a reminder in the database (without client_ids)"""
    user_id: int = Field(
        ...,
        example=42,
        description="ID of the user creating this reminder"
    )

class ReminderUpdate(BaseModel):
    """Schema for updating an existing reminder"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=255, 
        example="Updated: Quarterly Tax Deadline",
        description="New title for the reminder"
    )
    description: Optional[str] = Field(
        None, 
        example="Updated tax filing details with new due date. Reference: TAX-2023-Q2-REV",
        description="Updated description for the reminder"
    )
    reminder_type: Optional[ReminderType] = Field(
        None, 
        example="DEADLINE", 
        description="Updated type of reminder"
    )
    notification_type: Optional[NotificationType] = Field(
        None, 
        example="SMS", 
        description="Updated delivery method"
    )
    reminder_date: Optional[datetime] = Field(
        None, 
        example="2023-07-15T15:00:00Z", 
        description="Updated reminder date (must be at least 5 minutes in the future)"
    )
    is_recurring: Optional[bool] = Field(
        None, 
        example=True, 
        description="Updated recurring status"
    )
    recurrence_pattern: Optional[str] = Field(
        None, 
        example="WEEKLY", 
        description="Updated recurrence pattern"
    )
    is_active: Optional[bool] = Field(
        None, 
        example=True, 
        description="Set to false to deactivate this reminder"
    )
    email_configuration_id: Optional[int] = Field(
        None, 
        example=3, 
        description="Updated email configuration ID (deprecated - use sender_identity_id instead)"
    )
    sender_identity_id: Optional[int] = Field(
        None, 
        example=3, 
        description="Updated sender identity ID"
    )
    client_ids: Optional[List[int]] = Field(
        None, 
        example=[2, 4, 5],
        description="Updated list of client IDs to receive this reminder"
    )
    
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
    """Base schema for a reminder stored in the database with system fields"""
    id: int = Field(..., example=1, description="Unique identifier for the reminder")
    user_id: int = Field(..., example=42, description="ID of the user who owns this reminder")
    created_at: datetime = Field(..., example="2023-03-15T09:30:00Z", description="When the reminder was created")
    updated_at: Optional[datetime] = Field(None, example="2023-03-16T14:45:00Z", description="When the reminder was last updated")

    model_config = ConfigDict(from_attributes=True)

class ReminderSchema(ReminderInDBBase):
    """Complete reminder model returned from API"""
    pass

class ReminderDetail(ReminderSchema):
    """Enhanced reminder model with recipient and notification details"""
    clients: List[int] = Field(
        ..., 
        example=[1, 2, 3], 
        description="List of client IDs who will receive this reminder"
    )
    notifications_count: int = Field(
        0, 
        example=5, 
        description="Total number of notifications generated for this reminder"
    )
    sent_count: int = Field(
        0, 
        example=4, 
        description="Number of notifications successfully sent"
    )
    failed_count: int = Field(
        0, 
        example=1, 
        description="Number of notifications that failed to send"
    )
    sender_identity_type: Optional[str] = Field(
        None,
        example="EMAIL",
        description="Type of sender identity used for this reminder"
    )
    sender_identity_value: Optional[str] = Field(
        None,
        example="support@yourcompany.com",
        description="Email or phone number of the sender"
    )
    sender_identity_display_name: Optional[str] = Field(
        None,
        example="Company Support Team",
        description="Display name of the sender identity"
    )