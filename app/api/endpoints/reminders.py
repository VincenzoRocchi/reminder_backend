from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.reminders import NotificationTypeEnum
from app.schemas.reminders import Reminder, ReminderCreate, ReminderUpdate, ReminderDetail
from app.core.exceptions import AppException
from app.services.reminder import reminder_service

router = APIRouter()

@router.get("/", response_model=List[Reminder])
async def read_reminders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    service_account_id: int = None,
):
    """
    Retrieve reminders for the current user.
    Optionally filter by active status or service account.
    """
    return reminder_service.get_user_reminders(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        active_only=active_only,
        service_account_id=service_account_id
    )

@router.post("/", response_model=ReminderDetail, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: Annotated[ReminderCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new reminder with client associations.
    """
    return reminder_service.create_reminder(
        db,
        reminder_in=reminder_in,
        user_id=current_user.id
    )

@router.get("/{reminder_id}", response_model=ReminderDetail)
async def read_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific reminder by ID with client details.
    """
    return reminder_service.get_reminder_with_stats(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )

@router.put("/{reminder_id}", response_model=ReminderDetail)
async def update_reminder(
    reminder_id: int,
    reminder_in: Annotated[ReminderUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a reminder and its client associations.
    """
    return reminder_service.update_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id,
        reminder_in=reminder_in
    )

@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a reminder.
    """
    reminder_service.delete_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    return {"detail": "Reminder deleted successfully"}

@router.post("/{reminder_id}/send-now", response_model=dict)
async def send_reminder_now(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Trigger immediate sending of a reminder.
    """
    reminder_service.send_reminder_now(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    return {
        "status": "success",
        "message": "Reminder queued for immediate sending",
        "reminder_id": reminder_id
    }