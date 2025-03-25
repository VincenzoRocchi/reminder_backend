from typing import List, Annotated
import datetime
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.reminders import Reminder as ReminderModel
from app.models.notifications import Notification as NotificationModel, NotificationStatusEnum
from app.schemas.notifications import Notification, NotificationUpdate, NotificationDetail

router = APIRouter()

@router.get("/", response_model=List[Notification])
async def read_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    reminder_id: int = None,
    client_id: int = None,
    status: str = None,
):
    """
    Retrieve notifications for the current user.
    Filter by reminder, client, or status if provided.
    """
    # Base query: get notifications from reminders owned by the current user
    query = db.query(NotificationModel).join(
        ReminderModel,
        NotificationModel.reminder_id == ReminderModel.id
    ).filter(
        ReminderModel.user_id == current_user.id
    )
    
    # Apply filters
    if reminder_id:
        query = query.filter(NotificationModel.reminder_id == reminder_id)
    
    if client_id:
        query = query.filter(NotificationModel.client_id == client_id)
    
    if status:
        try:
            status_enum = NotificationStatusEnum(status)
            query = query.filter(NotificationModel.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {status}"
            )
    
    # Order by most recent first
    query = query.order_by(NotificationModel.created_at.desc())
    
    # Apply pagination
    notifications = query.offset(skip).limit(limit).all()
    
    return notifications

@router.get("/{notification_id}", response_model=NotificationDetail)
async def read_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific notification by ID.
    """
    # Join with reminder to check ownership
    notification = db.query(NotificationModel).join(
        ReminderModel,
        NotificationModel.reminder_id == ReminderModel.id
    ).filter(
        NotificationModel.id == notification_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Get reminder details
    reminder = db.query(ReminderModel).filter(
        ReminderModel.id == notification.reminder_id
    ).first()
    
    # Get client details (we'll need to import the Client model)
    client_name = "Unknown"  # In production, get this from the client
    
    # Create detailed response
    notification_detail = NotificationDetail(
        **notification.__dict__,
        reminder_title=reminder.title,
        client_name=client_name
    )
    
    return notification_detail

@router.put("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: int,
    notification_in: Annotated[NotificationUpdate, Body],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a notification status, sent_at, or error_message.
    """
    # Join with reminder to check ownership
    notification = db.query(NotificationModel).join(
        ReminderModel,
        NotificationModel.reminder_id == ReminderModel.id
    ).filter(
        NotificationModel.id == notification_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Update fields
    update_data = notification_in.model_dump(exclude_unset=True)
    
    # Convert status string to enum if provided
    if "status" in update_data:
        try:
            update_data["status"] = NotificationStatusEnum(update_data["status"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status value: {update_data['status']}"
            )
    
    for field, value in update_data.items():
        setattr(notification, field, value)
    
    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return notification

@router.post("/{notification_id}/resend", response_model=dict)
async def resend_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Resend a failed notification.
    """
    # Join with reminder to check ownership
    notification = db.query(NotificationModel).join(
        ReminderModel,
        NotificationModel.reminder_id == ReminderModel.id
    ).filter(
        NotificationModel.id == notification_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Only allow resending failed notifications
    if notification.status != NotificationStatusEnum.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only resend failed notifications. Current status: {notification.status.value}"
        )
    
    # Reset status to pending
    notification.status = NotificationStatusEnum.PENDING
    notification.error_message = None  # Clear error message
    
    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    # In production, this would trigger the scheduler to pick up the notification
    return {
        "status": "success",
        "message": "Notification queued for resending",
        "notification_id": notification.id
    }