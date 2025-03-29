from typing import List, Annotated, Optional
from fastapi import APIRouter, Body, Depends, status, Query, Path, Security
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_current_user, get_current_active_superuser
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.notifications import NotificationStatusEnum
from app.schemas.notifications import NotificationSchema, NotificationUpdate, NotificationDetail, NotificationCreate
from app.core.exceptions import AppException
from app.services.notification import notification_service

router = APIRouter()

# User-specific endpoints
@router.get("/", response_model=List[NotificationDetail])
async def read_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    reminder_id: Optional[int] = Query(None, description="Filter by reminder ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    status: Optional[str] = Query(None, description="Filter by notification status (PENDING, SENT, FAILED)"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    start_date: Optional[datetime] = Query(None, description="Filter by notifications created after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter by notifications created before this date"),
):
    """
    Retrieve detailed notifications for the current user with comprehensive filtering options.
    
    This endpoint:
    - Returns a list of notifications created for the authenticated user's reminders
    - Includes detailed information about related entities (reminder, client)
    - Provides powerful filtering capabilities for specific queries
    - Supports pagination for handling large result sets
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    - reminder_id: Filter notifications by a specific reminder
    - client_id: Filter notifications by a specific client
    - status: Filter by notification status (PENDING, SENT, FAILED, CANCELLED)
    - notification_type: Filter by notification type (EMAIL, SMS, WHATSAPP)
    - start_date: Filter by notifications created after this date (ISO 8601 format)
    - end_date: Filter by notifications created before this date (ISO 8601 format)
    
    Returns:
    - List of detailed notification objects including reminder and client information
    
    Notes:
    - Results are sorted by created_at in descending order (newest first)
    - Invalid status values will result in a 400 Bad Request error
    - Date filters accept ISO 8601 format (e.g., "2023-12-31T23:59:59Z")
    - For notification counts by status, use the /count endpoint
    - For a specific notification's details, use the GET /{notification_id} endpoint
    """
    if status:
        try:
            status_enum = NotificationStatusEnum(status)
        except ValueError:
            raise AppException(
                message=f"Invalid status value: {status}",
                code="INVALID_STATUS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    else:
        status_enum = None

    return notification_service.get_detailed_user_notifications(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        reminder_id=reminder_id,
        client_id=client_id,
        status=status_enum,
        notification_type=notification_type,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/count", response_model=dict)
async def count_user_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a summary count of notifications by status for the current user.
    
    This endpoint:
    - Retrieves aggregated counts of notifications for the authenticated user
    - Categorizes counts by notification status
    - Provides a quick overview of notification activity
    
    Returns:
    - A dictionary containing counts with the following structure:
      - pending: Number of notifications waiting to be sent
      - sent: Number of successfully delivered notifications
      - failed: Number of notifications that failed to deliver
      - cancelled: Number of notifications that were cancelled
      - total: Total number of notifications across all statuses
    
    Notes:
    - This endpoint is optimized for performance and suitable for dashboards
    - Only includes notifications owned by the authenticated user
    - No pagination or filtering options are available for this summary endpoint
    - For detailed notification information, use the main GET / endpoint
    """
    counts = notification_service.get_user_notification_counts(
        db,
        user_id=current_user.id
    )
    
    return counts

@router.get("/filters", response_model=List[NotificationSchema])
async def filter_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    reminder_id: Optional[int] = None,
    client_id: Optional[int] = None,
    notification_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = Query(None, description="Filter by notifications created after this date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by notifications created before this date (ISO format)"),
):
    """
    Advanced filtering of notifications with multiple criteria and precise date ranges.
    
    This endpoint:
    - Provides flexible filtering capabilities similar to the main endpoint
    - Returns a simplified notification schema (without full detail objects)
    - Optimized for scenarios requiring basic notification information
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    - reminder_id: Filter by specific reminder ID
    - client_id: Filter by specific client ID
    - notification_type: Filter by notification type (EMAIL, SMS, WHATSAPP)
    - status: Filter by notification status (PENDING, SENT, FAILED, CANCELLED)
    - start_date: Filter by notifications created after this date (ISO 8601 format)
    - end_date: Filter by notifications created before this date (ISO 8601 format)
    
    Returns:
    - List of basic notification objects (without detailed related entity information)
    
    Notes:
    - This endpoint returns a more lightweight schema than the main GET / endpoint
    - All filters are optional and can be combined for precise queries
    - Invalid status values will result in a 400 Bad Request error
    - Results are sorted by created_at in descending order (newest first)
    - For full details including related entities, use the main GET / endpoint
    """
    # Parse status enum if provided
    status_enum = None
    if status:
        try:
            status_enum = NotificationStatusEnum(status)
        except ValueError:
            raise AppException(
                message=f"Invalid status value: {status}",
                code="INVALID_STATUS",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    return notification_service.filter_notifications(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        reminder_id=reminder_id,
        client_id=client_id,
        notification_type=notification_type,
        status=status_enum,
        start_date=start_date,
        end_date=end_date
    )

@router.get("/{notification_id}", response_model=NotificationDetail)
async def read_notification(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    notification_id: int = Path(..., description="The ID of the notification to retrieve"),
):
    """
    Get detailed information about a specific notification by ID.
    
    This endpoint:
    - Retrieves complete information about a single notification
    - Includes details about the associated reminder and client
    - Performs ownership validation to ensure the notification belongs to the current user
    
    Parameters:
    - notification_id: The unique identifier of the notification to retrieve
    
    Returns:
    - Detailed notification object including:
      - Basic notification information (status, type, timestamps)
      - Related reminder details
      - Related client information
      - Any error messages or delivery information
    
    Notes:
    - Returns 404 if the notification doesn't exist
    - Returns 404 if the notification doesn't belong to the authenticated user
    - Provides the most comprehensive view of a notification including all related entities
    - Use this endpoint when you need complete information about a specific notification
    """
    return notification_service.get_notification_detail(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )

@router.post("/admin/create", response_model=NotificationSchema, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_in: Annotated[NotificationCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    [Admin Only] Manually create a new notification record.
    
    This endpoint:
    - Creates a notification directly, bypassing the normal reminder-based workflow
    - Restricted to superusers/administrators only
    - Useful for testing, debugging, or special operational cases
    
    Required fields:
    - reminder_id: ID of the related reminder
    - client_id: ID of the client to receive the notification
    - notification_type: Type of notification (EMAIL, SMS, WHATSAPP)
    
    Optional fields:
    - status: Initial status (defaults to PENDING)
    - sent_at: When the notification was sent (for manual status updates)
    - error_message: Error details if status is FAILED
    - custom_data: Any additional information to store with the notification
    
    Returns:
    - Created notification object
    
    Notes:
    - This endpoint is intended for administrative purposes only
    - Normal notification creation should happen through the reminder system
    - The user creating the notification must have superuser privileges
    - The reminder and client must exist in the system
    """
    return notification_service.create_notification(
        db,
        notification_in=notification_in,
        user_id=current_user.id
    )

@router.put("/{notification_id}", response_model=NotificationSchema)
async def update_notification(
    notification_id: int,
    notification_in: Annotated[NotificationUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update specific fields of an existing notification.
    
    This endpoint:
    - Allows updating sent_at timestamp or error_message for an existing notification
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns the updated notification
    
    Parameters:
    - notification_id: The unique identifier of the notification to update
    
    Available fields to update:
    - sent_at: When the notification was sent (datetime)
    - error_message: Detailed error information if the notification failed
    - custom_data: Any additional data associated with the notification
    
    Returns:
    - Updated notification object
    
    Notes:
    - All fields are optional - only specified fields will be updated
    - For status changes, use the dedicated endpoints:
      - /notifications/{id}/mark-as-sent
      - /notifications/{id}/mark-as-failed
      - /notifications/{id}/mark-as-cancelled
    - Returns 404 if the notification doesn't exist or doesn't belong to the user
    - Cannot update notification_type, reminder_id, or client_id (these are immutable)
    """
    return notification_service.update_notification(
        db,
        notification_id=notification_id,
        user_id=current_user.id,
        notification_in=notification_in
    )

@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
async def delete_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Permanently delete a notification from the system.
    
    This endpoint:
    - Completely removes the notification from the database
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns a confirmation message upon successful deletion
    
    Parameters:
    - notification_id: The unique identifier of the notification to delete
    
    Notes:
    - This is a destructive operation that cannot be undone
    - Consider using mark-as-cancelled instead if you want to preserve notification history
    - Returns 404 if the notification doesn't exist or doesn't belong to the authenticated user
    - For bulk deletion, use the /batch/delete endpoint
    """
    notification_service.delete_notification(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    return {"detail": "Notification deleted successfully"}

@router.post("/{notification_id}/resend", response_model=dict)
async def resend_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Attempt to resend a previously failed notification.
    
    This endpoint:
    - Resets a failed notification to PENDING status
    - Queues it for delivery via the notification system
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns a confirmation message
    
    Parameters:
    - notification_id: The unique identifier of the notification to resend
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - notification_id: ID of the notification that was queued for resending
    
    Notes:
    - Only failed notifications can be resent
    - Attempting to resend a non-failed notification will result in an error
    - The notification will be processed by the background worker
    - Returns 404 if the notification doesn't exist or doesn't belong to the authenticated user
    - For bulk resending of failed notifications, use the /batch/resend-failed endpoint
    """
    notification_service.resend_notification(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    return {
        "status": "success",
        "message": "Notification queued for resending",
        "notification_id": notification_id
    }

@router.post("/{notification_id}/mark-as-sent", response_model=NotificationSchema)
async def mark_notification_as_sent(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Manually mark a notification as successfully sent.
    
    This endpoint:
    - Updates a notification's status to SENT
    - Sets the sent_at timestamp to the current time
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns the updated notification
    
    Parameters:
    - notification_id: The unique identifier of the notification to mark as sent
    
    Returns:
    - Updated notification object with status=SENT and current sent_at timestamp
    
    Notes:
    - This endpoint is typically used for manual status updates
    - Useful when a notification was sent through an external system
    - Automatic notifications will be marked as sent by the system
    - Returns 404 if the notification doesn't exist or doesn't belong to the authenticated user
    - Only PENDING notifications can be marked as sent
    """
    return notification_service.mark_as_sent(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )

@router.post("/{notification_id}/mark-as-failed", response_model=NotificationSchema)
async def mark_notification_as_failed(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    error_message: str = Query(..., description="Error message explaining the failure"),
):
    """
    Manually mark a notification as failed with a specific error message.
    
    This endpoint:
    - Updates a notification's status to FAILED
    - Sets the provided error message
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns the updated notification
    
    Parameters:
    - notification_id: The unique identifier of the notification to mark as failed
    - error_message: Description of why the notification failed (required query parameter)
    
    Returns:
    - Updated notification object with status=FAILED and the provided error message
    
    Notes:
    - This endpoint is typically used for manual status updates
    - Automatic notifications will be marked as failed by the system if delivery fails
    - The error_message parameter is required to provide context for the failure
    - Returns 404 if the notification doesn't exist or doesn't belong to the authenticated user
    - Only PENDING notifications can be marked as failed
    """
    return notification_service.mark_as_failed(
        db,
        notification_id=notification_id,
        user_id=current_user.id,
        error_message=error_message
    )

@router.post("/{notification_id}/mark-as-cancelled", response_model=NotificationSchema)
async def mark_notification_as_cancelled(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Mark a pending notification as cancelled to prevent it from being sent.
    
    This endpoint:
    - Updates a notification's status to CANCELLED
    - Prevents it from being processed by the notification system
    - Performs ownership validation to ensure the notification belongs to the current user
    - Returns the updated notification
    
    Parameters:
    - notification_id: The unique identifier of the notification to cancel
    
    Returns:
    - Updated notification object with status=CANCELLED
    
    Notes:
    - Only PENDING notifications can be cancelled
    - Attempting to cancel already sent or failed notifications will result in an error
    - This operation cannot be undone - cancelled notifications cannot be reactivated
    - Returns 404 if the notification doesn't exist or doesn't belong to the authenticated user
    - For bulk cancellation, use the /batch/cancel-pending endpoint
    """
    return notification_service.mark_as_cancelled(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )

@router.post("/batch/resend-failed", response_model=dict)
async def batch_resend_failed_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    limit: int = Query(10, description="Maximum number of notifications to resend"),
):
    """
    Resend multiple failed notifications in a single operation.
    
    This endpoint:
    - Identifies all failed notifications belonging to the current user
    - Resets them to PENDING status and queues them for delivery
    - Limits the number of notifications processed according to the limit parameter
    - Returns a summary of the operation
    
    Parameters:
    - limit: Maximum number of failed notifications to resend (default: 10)
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - count: Number of notifications queued for resending
    
    Notes:
    - This endpoint only processes notifications with FAILED status
    - Notifications are selected based on creation date (oldest first)
    - The operation respects the specified limit to prevent system overload
    - Returns an empty count (0) if no failed notifications are found
    - Does not require specifying individual notification IDs
    - The notifications will be processed by the background worker
    """
    count = notification_service.batch_resend_failed_notifications(
        db,
        user_id=current_user.id,
        limit=limit
    )
    
    return {
        "status": "success",
        "message": f"{count} failed notifications queued for resending",
        "count": count
    }

# Superuser-only endpoints
@router.get("/admin/all", response_model=List[NotificationSchema])
async def read_all_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    reminder_id: Optional[int] = Query(None, description="Filter by reminder ID"),
    client_id: Optional[int] = Query(None, description="Filter by client ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by notification status"),
):
    """
    [Admin Only] Retrieve notifications across all users with comprehensive filtering.
    
    This endpoint:
    - Provides system-wide access to all notification records
    - Restricted to superusers/administrators only
    - Supports filtering by various criteria including user ID
    - Returns basic notification information without detailed related entities
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    - reminder_id: Filter by specific reminder ID
    - client_id: Filter by specific client ID
    - user_id: Filter by specific user ID (unique to admin endpoints)
    - status: Filter by notification status (PENDING, SENT, FAILED, CANCELLED)
    
    Returns:
    - List of notification objects across all users matching the filter criteria
    
    Notes:
    - This endpoint requires superuser privileges
    - Results are sorted by created_at in descending order (newest first)
    - Invalid status values will result in a 400 Bad Request error
    - The user_id filter allows administrators to view notifications for specific users
    - For system-wide notification statistics, use the /admin/stats endpoint
    """
    status_enum = None
    if status:
        try:
            status_enum = NotificationStatusEnum(status)
        except ValueError:
            raise AppException(
                message=f"Invalid status value: {status}",
                code="INVALID_STATUS",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    return notification_service.get_all_notifications(
        db,
        skip=skip,
        limit=limit,
        reminder_id=reminder_id,
        client_id=client_id,
        user_id=user_id,
        status=status_enum
    )

@router.post("/generate-for-reminder/{reminder_id}", response_model=List[NotificationSchema])
async def generate_notifications_for_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Generate pending notifications for a reminder without immediately sending them.
    
    This endpoint:
    - Creates notification records for each client associated with the specified reminder
    - Sets all notifications to PENDING status
    - Performs ownership validation to ensure the reminder belongs to the current user
    - Returns the list of created notification objects
    
    Parameters:
    - reminder_id: The unique identifier of the reminder to generate notifications for
    
    Returns:
    - List of newly created notification objects with PENDING status
    
    Notes:
    - This endpoint only creates notification records without sending them
    - Useful for preparing notifications that will be sent later by a scheduled job
    - Requires an active reminder with at least one associated client
    - Returns 404 if the reminder doesn't exist or doesn't belong to the authenticated user
    - To actually send the notifications, use the /reminders/{id}/send-now endpoint
    """
    return notification_service.generate_notifications_for_reminder(
        db,
        reminder_id=reminder_id,
        user_id=current_user.id
    )

@router.post("/batch/cancel-pending", response_model=dict)
async def batch_cancel_pending_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    reminder_id: Optional[int] = None,
    client_id: Optional[int] = None,
    limit: int = Query(100, description="Maximum number of notifications to cancel"),
):
    """
    Cancel multiple pending notifications in a single operation with optional filtering.
    
    This endpoint:
    - Updates the status of pending notifications to CANCELLED
    - Supports filtering to target specific notifications
    - Limits the number of notifications processed according to the limit parameter
    - Returns a summary of the operation
    
    Parameters:
    - reminder_id: Optional filter to cancel notifications for a specific reminder only
    - client_id: Optional filter to cancel notifications for a specific client only
    - limit: Maximum number of notifications to cancel (default: 100)
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - count: Number of notifications that were cancelled
    
    Notes:
    - This endpoint only processes notifications with PENDING status
    - Filters can be combined (e.g., specific reminder AND specific client)
    - If no filters are provided, all pending notifications for the user will be cancelled
    - The operation respects the specified limit to prevent system overload
    - This operation cannot be undone - cancelled notifications cannot be reactivated
    """
    count = notification_service.batch_cancel_pending_notifications(
        db,
        user_id=current_user.id,
        reminder_id=reminder_id,
        client_id=client_id,
        limit=limit
    )
    
    return {
        "status": "success",
        "message": f"{count} pending notifications marked as cancelled",
        "count": count
    }

@router.delete("/batch/delete", response_model=dict)
async def batch_delete_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    reminder_id: Optional[int] = None,
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(50, description="Maximum number of notifications to delete"),
):
    """
    Delete multiple notifications in a single operation with flexible filtering options.
    
    This endpoint:
    - Permanently removes multiple notifications from the database
    - Supports filtering by reminder, client, and/or status
    - Limits the number of notifications processed according to the limit parameter
    - Returns a summary of the operation
    
    Parameters:
    - reminder_id: Optional filter to delete notifications for a specific reminder only
    - client_id: Optional filter to delete notifications for a specific client only
    - status: Optional filter to delete notifications with a specific status only
    - limit: Maximum number of notifications to delete (default: 50)
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - count: Number of notifications that were deleted
    
    Notes:
    - This is a destructive operation that cannot be undone
    - Filters can be combined for precise targeting
    - If no filters are provided, the oldest notifications will be deleted up to the limit
    - The operation respects the specified limit to prevent accidental mass deletion
    - Invalid status values will result in a 400 Bad Request error
    - Consider using selective filters to target specific notifications
    """
    status_enum = None
    if status:
        try:
            status_enum = NotificationStatusEnum(status)
        except ValueError:
            raise AppException(
                message=f"Invalid status value: {status}",
                code="INVALID_STATUS",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
    count = notification_service.batch_delete_notifications(
        db,
        user_id=current_user.id,
        reminder_id=reminder_id,
        client_id=client_id,
        status=status_enum,
        limit=limit
    )
    
    return {
        "status": "success",
        "message": f"{count} notifications deleted",
        "count": count
    }

@router.get("/admin/stats", response_model=dict)
async def get_notification_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
):
    """
    [Admin Only] Get comprehensive system-wide notification statistics.
    
    This endpoint:
    - Retrieves global statistics about notifications across all users
    - Provides counts by status, type, and delivery rates
    - Restricted to superusers/administrators only
    - Returns a detailed statistical breakdown
    
    Returns:
    - A dictionary containing various statistical metrics including:
      - total_count: Total number of notifications in the system
      - counts_by_status: Breakdown of notifications by status
      - counts_by_type: Breakdown of notifications by notification type
      - success_rate: Percentage of sent notifications vs total attempts
      - recent_activity: Counts of notifications in recent time periods
    
    Notes:
    - This endpoint requires superuser privileges
    - Optimized for dashboard displays and system monitoring
    - Provides a system-wide view of notification performance and activity
    - No filtering options are available for this summary endpoint
    """
    return notification_service.get_notification_stats(db)

@router.post("/admin/clear-failed", response_model=dict)
async def admin_clear_failed_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    older_than_days: int = Query(7, description="Clear failed notifications older than this many days"),
    limit: int = Query(1000, description="Maximum number of notifications to clear"),
):
    """
    [Admin Only] Delete failed notifications older than the specified number of days.
    
    This endpoint:
    - Removes old failed notifications from the database
    - Allows specifying an age threshold in days
    - Limits the number of notifications processed according to the limit parameter
    - Restricted to superusers/administrators only
    - Returns a summary of the operation
    
    Parameters:
    - older_than_days: Age threshold in days (default: 7)
    - limit: Maximum number of notifications to delete (default: 1000)
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - count: Number of notifications that were deleted
    
    Notes:
    - This endpoint requires superuser privileges
    - This is a destructive operation that cannot be undone
    - Only affects notifications with FAILED status
    - Useful for database maintenance and cleanup
    - The operation respects the specified limit to prevent system overload
    - A good practice is to run this regularly via a scheduled job
    """
    count = notification_service.clear_old_failed_notifications(
        db,
        older_than_days=older_than_days,
        limit=limit
    )
    
    return {
        "status": "success",
        "message": f"Cleared {count} failed notifications older than {older_than_days} days",
        "count": count
    }

@router.post("/admin/resend-all-failed", response_model=dict)
async def admin_resend_all_failed_notifications(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    limit: int = Query(100, description="Maximum number of notifications to resend"),
):
    """
    [Admin Only] Resend all failed notifications across all users in the system.
    
    This endpoint:
    - Identifies all failed notifications system-wide
    - Resets them to PENDING status and queues them for delivery
    - Limits the number of notifications processed according to the limit parameter
    - Restricted to superusers/administrators only
    - Returns a summary of the operation
    
    Parameters:
    - limit: Maximum number of failed notifications to resend (default: 100)
    
    Returns:
    - status: Operation result (success or error)
    - message: Human-readable description of the action taken
    - count: Number of notifications queued for resending
    
    Notes:
    - This endpoint requires superuser privileges
    - Only processes notifications with FAILED status
    - Useful for recovering from system-wide notification failures
    - Notifications are selected based on creation date (oldest first)
    - The operation respects the specified limit to prevent system overload
    - The notifications will be processed by the background worker
    """
    count = notification_service.resend_all_failed_notifications(
        db,
        limit=limit
    )
    
    return {
        "status": "success",
        "message": f"Requeued {count} failed notifications for sending",
        "count": count
    }