from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.reminder import Reminder as ReminderModel
from app.models.notification import Notification as NotificationModel
from app.schemas.notification import Notification, NotificationUpdate

router = APIRouter()


@router.get("/", response_model=List[Notification])
def read_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    reminder_id: int = None,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Retrieve notifications.
    Filter by reminder if reminder_id is provided.
    """
    query = db.query(NotificationModel)
    
    # Either notifications where the current user is the recipient
    # Or notifications for reminders created by the current user
    recipient_filter = NotificationModel.recipient_id == current_user.id
    creator_filter = (
        NotificationModel.reminder_id == ReminderModel.id,
        ReminderModel.created_by == current_user.id
    )
    
    query = query.filter(recipient_filter | creator_filter)
    
    # Filter by reminder
    if reminder_id:
        # Verify reminder access
        reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
        if not reminder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found",
            )
        if reminder.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access notifications for this reminder",
            )
        query = query.filter(NotificationModel.reminder_id == reminder_id)
    
    notifications = query.offset(skip).limit(limit).all()
    return notifications


@router.get("/{notification_id}", response_model=Notification)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a specific notification by ID.
    """
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    # Check if current user is authorized (recipient or reminder creator)
    if notification.recipient_id != current_user.id:
        reminder = db.query(ReminderModel).filter(ReminderModel.id == notification.reminder_id).first()
        if not reminder or reminder.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this notification",
            )
    
    return notification


@router.put("/{notification_id}", response_model=Notification)
def update_notification(
    notification_id: int,
    notification_in: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update a notification status, sent_at, or error_message.
    Only for admins or the creator of the related reminder.
    """
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    # Check if current user is authorized
    reminder = db.query(ReminderModel).filter(ReminderModel.id == notification.reminder_id).first()
    if not reminder or (reminder.created_by != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this notification",
        )
    
    # Update notification attributes
    update_data = notification_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(notification, key, value)
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification