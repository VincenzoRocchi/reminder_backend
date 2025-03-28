from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.reminders import NotificationTypeEnum
from app.schemas.reminders import ReminderSchema, ReminderCreate, ReminderUpdate, ReminderDetail
from app.core.exceptions import AppException
from app.services.reminder import reminder_service
from app.services.notification import notification_service

router = APIRouter()

@router.get("/", response_model=List[ReminderSchema])
async def read_reminders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    sender_identity_id: int = None,
):
    """
    Retrieve reminders for the current user.
    Optionally filter by active status or sender identity.
    """
    return reminder_service.get_user_reminders(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        active_only=active_only,
        sender_identity_id=sender_identity_id
    )

@router.post("/", response_model=ReminderDetail, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: Annotated[ReminderCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new reminder with client associations.
    
    - **reminder_type**: Supported values - PAYMENT, DEADLINE, NOTIFICATION
    - **notification_type**: Supported values - EMAIL, SMS, WHATSAPP
    - **reminder_date**: ISO 8601 datetime format (e.g., "2025-03-27T15:00:09.105Z")
      This is the date when the reminder should be sent, not the creation date.
      Examples:
        - "2025-03-27T15:00:00Z" (March 27, 2025 at 3:00 PM UTC)
        - "2025-12-31T23:59:59Z" (December 31, 2025 at 11:59 PM UTC)
    - **client_ids**: List of client IDs who should receive this reminder
    - **recurrence_pattern**: Only needed if is_recurring=True. Format suggestions: "DAILY", "WEEKLY", "MONTHLY"
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
    
    This endpoint:
    1. Creates notification records for each client associated with the reminder
    2. Attempts to send each notification immediately
    3. Updates notification statuses based on success/failure
    """
    # First generate notifications for all clients associated with this reminder
    notifications = notification_service.generate_notifications_for_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    # Then trigger the service to send the notifications
    reminder_service.send_reminder_now(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    
    return {
        "status": "success",
        "message": f"Reminder queued for immediate sending to {len(notifications)} recipients",
        "reminder_id": reminder_id,
        "notification_count": len(notifications)
    }

@router.post("/{reminder_id}/clients", response_model=ReminderDetail)
async def add_clients_to_reminder(
    reminder_id: int,
    client_ids: Annotated[List[int], Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Add clients to an existing reminder.
    
    - **client_ids**: List of client IDs to add to the reminder
    
    Returns the updated reminder with client details.
    """
    reminder_service.add_clients_to_reminder(
        db,
        reminder_id=reminder_id,
        client_ids=client_ids,
        user_id=current_user.id
    )
    
    return reminder_service.get_reminder_with_stats(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )

@router.delete("/{reminder_id}/clients", response_model=ReminderDetail)
async def remove_clients_from_reminder(
    reminder_id: int,
    client_ids: Annotated[List[int], Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Remove clients from an existing reminder.
    
    - **client_ids**: List of client IDs to remove from the reminder
    
    Returns the updated reminder with client details.
    """
    reminder_service.remove_clients_from_reminder(
        db,
        reminder_id=reminder_id,
        client_ids=client_ids,
        user_id=current_user.id
    )
    
    return reminder_service.get_reminder_with_stats(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )