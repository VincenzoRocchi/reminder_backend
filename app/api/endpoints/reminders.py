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
    Retrieve all reminders belonging to the current user.
    
    This endpoint:
    - Returns a list of all reminders created by the authenticated user
    - Supports pagination with skip and limit parameters
    - Provides optional filtering by active status and sender identity
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    - active_only: If true, only returns active reminders
    - sender_identity_id: Optional filter by sender identity ID
    
    Returns:
    - List of reminder objects with basic information
    
    Notes:
    - Results are sorted by reminder_date in ascending order
    - Only returns reminders owned by the authenticated user
    - For detailed information about a specific reminder, use the GET /{reminder_id} endpoint
    - Does not include statistics or client details in the response
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
    
    This endpoint:
    - Creates a new reminder record associated with the authenticated user
    - Associates the reminder with one or more clients
    - Validates that the notification type is compatible with the sender identity
    - Returns the created reminder with client details
    
    Required fields:
    - title: The title or subject of the reminder
    - message: The content of the reminder
    - reminder_type: Type of reminder (DEADLINE or NOTIFICATION)
    - notification_type: Type of notification to send (EMAIL, SMS, or WHATSAPP)
    - reminder_date: When the reminder should be sent (ISO 8601 format)
    - sender_identity_id: ID of the sender identity to use
    - client_ids: List of client IDs who should receive this reminder
    
    Optional fields:
    - is_recurring: Whether this is a recurring reminder (defaults to false)
    - recurrence_pattern: Pattern for recurring reminders (e.g., "DAILY", "WEEKLY", "MONTHLY")
    - custom_fields: Any additional data to store with the reminder
    
    Notes:
    - The notification_type must be compatible with the sender identity type:
      - For EMAIL sender identities: only EMAIL notification type is allowed
      - For PHONE sender identities: SMS and WHATSAPP notification types are allowed
    - The reminder_date must be in ISO 8601 format (e.g., "2025-03-27T15:00:00Z")
    - The sender identity must be verified and complete before use
    - Each client in client_ids must belong to the current user
    - Recurring reminders require a recurrence_pattern
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
    Get detailed information about a specific reminder by ID.
    
    This endpoint:
    - Retrieves complete information about a single reminder
    - Includes client details and statistics
    - Performs ownership validation to ensure the reminder belongs to the current user
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to retrieve
    
    Returns:
    - Detailed reminder object including:
      - Basic reminder information
      - List of associated clients
      - Notification statistics
      - Recurrence information (if applicable)
    
    Notes:
    - Returns 404 if the reminder doesn't exist
    - Returns 404 if the reminder doesn't belong to the authenticated user
    - Includes a count of sent notifications and their status
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
    Update an existing reminder's information.
    
    This endpoint:
    - Updates specified fields for an existing reminder
    - Validates notification type compatibility with sender identity if changed
    - Performs ownership validation to ensure the reminder belongs to the current user
    - Returns the updated reminder with client details
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to update
    
    Available fields to update:
    - title: Updated title or subject
    - message: Updated content
    - reminder_type: Updated type (DEADLINE or NOTIFICATION)
    - notification_type: Updated notification method (EMAIL, SMS, WHATSAPP)
    - reminder_date: Updated date/time to send the reminder
    - sender_identity_id: Updated sender identity to use
    - is_recurring: Updated recurrence status
    - recurrence_pattern: Updated pattern for recurring reminders
    - is_active: Updated active status
    - custom_fields: Updated additional data
    
    Notes:
    - All fields are optional - only specified fields will be updated
    - If changing notification_type or sender_identity_id, compatibility is re-validated
    - If changing is_recurring to true, a recurrence_pattern must be provided
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    - To modify client associations, use the dedicated endpoints for adding/removing clients
    """
    return reminder_service.update_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id,
        reminder_in=reminder_in
    )

@router.delete("/{reminder_id}", status_code=status.HTTP_200_OK)
async def delete_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Permanently delete a reminder from the system.
    
    This endpoint:
    - Completely removes the reminder and all associated data from the database
    - Performs ownership validation to ensure the reminder belongs to the current user
    - Returns a confirmation message upon successful deletion
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to delete
    
    Notes:
    - This is a destructive operation that cannot be undone
    - Associated data like client associations and scheduled notifications will be deleted
    - Consider using the update endpoint to set is_active=false instead of deletion
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    """
    reminder_service.delete_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )
    return {"detail": "Reminder deleted successfully"}

@router.post("/{reminder_id}/send-now", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def send_reminder_now(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Trigger immediate sending of a reminder to all associated clients.
    
    This endpoint:
    - Bypasses the scheduled reminder_date and sends notifications immediately
    - Creates notification records for each client associated with the reminder
    - Queues the notifications for immediate delivery
    - Returns a summary of the operation
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to send
    
    Returns:
    - status: Operation status (success or error)
    - message: Description of the action taken
    - reminder_id: The ID of the reminder that was sent
    - notification_count: Number of notifications generated
    
    Notes:
    - Requires an active reminder with at least one associated client
    - The sender identity must be verified and properly configured
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    - This operation creates notification records regardless of the reminder's scheduled date
    - Actual delivery time may vary slightly depending on system load
    - Use the notification endpoints to check delivery status
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
    Add one or more clients to an existing reminder.
    
    This endpoint:
    - Associates additional clients with an existing reminder
    - Validates that each client belongs to the current user
    - Returns the updated reminder with complete client details
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to modify
    
    Required body:
    - client_ids: List of client IDs to add to the reminder
    
    Returns:
    - Updated reminder object with complete details including the added clients
    
    Notes:
    - Clients already associated with the reminder will be ignored (no duplicates)
    - Each client ID must belong to the authenticated user
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    - Returns 404 if any client doesn't exist or doesn't belong to the authenticated user
    - Does not affect already scheduled notifications (only affects future sends)
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
    Remove one or more clients from an existing reminder.
    
    This endpoint:
    - Disassociates specified clients from an existing reminder
    - Performs ownership validation for both reminder and clients
    - Returns the updated reminder with remaining client details
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to modify
    
    Required body:
    - client_ids: List of client IDs to remove from the reminder
    
    Returns:
    - Updated reminder object with complete details excluding the removed clients
    
    Notes:
    - Clients not associated with the reminder will be ignored
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    - Will not affect notifications that have already been sent
    - Will cancel any pending notifications to the removed clients
    - A reminder with no clients can still exist but cannot be sent
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