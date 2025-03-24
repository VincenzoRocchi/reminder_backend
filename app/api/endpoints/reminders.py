from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.business import Business as BusinessModel
from app.models.reminder import Reminder as ReminderModel
from app.models.notification import Notification as NotificationModel
from app.schemas.reminders import Reminder, ReminderCreate, ReminderUpdate, ReminderDetail

router = APIRouter()


@router.get("/", response_model=List[Reminder])
def read_reminders(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    business_id: int = None,
    current_user: UserModel = Depends(get_current_user),
):
    """
    Retrieve reminders.
    Filter by business if business_id is provided.
    """
    query = db.query(ReminderModel)
    
    # Filter by created_by (current user)
    query = query.filter(ReminderModel.created_by == current_user.id)
    
    # Filter by business
    if business_id:
        # Verify business ownership
        business = db.query(BusinessModel).filter(BusinessModel.id == business_id).first()
        if not business or (business.owner_id != current_user.id and not current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this business",
            )
        query = query.filter(ReminderModel.business_id == business_id)
    
    reminders = query.offset(skip).limit(limit).all()
    return reminders


@router.post("/", response_model=ReminderDetail)
def create_reminder(
    reminder_in: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Create new reminder and associated notifications.
    """
    # Check if business exists and user has access to it
    business = db.query(BusinessModel).filter(BusinessModel.id == reminder_in.business_id).first()
    if not business or (business.owner_id != current_user.id and not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create a reminder for this business",
        )
    
    # Create reminder
    reminder_data = reminder_in.dict(exclude={"recipient_ids"})
    reminder = ReminderModel(**reminder_data, created_by=current_user.id)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    # Create notifications for each recipient
    notifications = []
    for recipient_id in reminder_in.recipient_ids:
        # Verify recipient exists
        recipient = db.query(UserModel).filter(UserModel.id == recipient_id).first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient with ID {recipient_id} not found",
            )
        
        notification = NotificationModel(
            reminder_id=reminder.id,
            recipient_id=recipient_id,
            notification_type=reminder.notification_type,
            message=reminder.description
        )
        db.add(notification)
        notifications.append(notification)
    
    db.commit()
    
    # Return reminder with recipient IDs
    result = ReminderDetail(
        **reminder.__dict__,
        recipients=[n.recipient_id for n in notifications]
    )
    return result


@router.get("/{reminder_id}", response_model=ReminderDetail)
def read_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get a specific reminder by ID with recipient information.
    """
    reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    
    # Check if current user is authorized (creator or business owner)
    business = db.query(BusinessModel).filter(BusinessModel.id == reminder.business_id).first()
    if (reminder.created_by != current_user.id and 
        (not business or business.owner_id != current_user.id) and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this reminder",
        )
    
    # Get recipient IDs
    notifications = db.query(NotificationModel).filter(
        NotificationModel.reminder_id == reminder.id
    ).all()
    recipient_ids = [n.recipient_id for n in notifications]
    
    # Create detailed response
    result = ReminderDetail(
        **reminder.__dict__,
        recipients=recipient_ids
    )
    return result


@router.put("/{reminder_id}", response_model=ReminderDetail)
def update_reminder(
    reminder_id: int,
    reminder_in: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update a reminder and its recipients.
    """
    reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    
    # Check if current user is authorized
    business = db.query(BusinessModel).filter(BusinessModel.id == reminder.business_id).first()
    if (reminder.created_by != current_user.id and 
        (not business or business.owner_id != current_user.id) and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this reminder",
        )
    
    # Update reminder attributes
    update_data = reminder_in.dict(exclude={"recipient_ids"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)
    
    # Update recipients if provided
    if reminder_in.recipient_ids is not None:
        # Delete existing notifications
        db.query(NotificationModel).filter(
            NotificationModel.reminder_id == reminder.id
        ).delete()
        
        # Create new notifications
        for recipient_id in reminder_in.recipient_ids:
            notification = NotificationModel(
                reminder_id=reminder.id,
                recipient_id=recipient_id,
                notification_type=reminder.notification_type,
                message=reminder.description
            )
            db.add(notification)
    
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    # Get updated recipient IDs
    notifications = db.query(NotificationModel).filter(
        NotificationModel.reminder_id == reminder.id
    ).all()
    recipient_ids = [n.recipient_id for n in notifications]
    
    # Create detailed response
    result = ReminderDetail(
        **reminder.__dict__,
        recipients=recipient_ids
    )
    return result


@router.delete("/{reminder_id}", response_model=Reminder)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a reminder.
    """
    reminder = db.query(ReminderModel).filter(ReminderModel.id == reminder_id).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )
    
    # Check if current user is authorized
    business = db.query(BusinessModel).filter(BusinessModel.id == reminder.business_id).first()
    if (reminder.created_by != current_user.id and 
        (not business or business.owner_id != current_user.id) and 
        not current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this reminder",
        )
    
    db.delete(reminder)
    db.commit()
    return reminder