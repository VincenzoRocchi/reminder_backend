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
    Retrieve notifications for the current user with flexible filtering options.
    
    This endpoint supports filtering by:
    - reminder_id: Get notifications for a specific reminder
    - client_id: Get notifications for a specific client
    - status: Get notifications with a specific status (PENDING, SENT, FAILED)
    - notification_type: Filter by notification type
    - start_date: Filter by notifications created after this date
    - end_date: Filter by notifications created before this date
    
    The response includes detailed information about related entities (reminder, client).
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
    Get counts of notifications by status for the current user.
    
    Returns a summary of pending, sent, failed, and total notifications.
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
    Advanced filtering of notifications with multiple parameters.
    
    All filters are optional and can be combined for precise queries.
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
    Get a specific notification by ID with detailed information.
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
    [Admin Only] Manually create a new notification.
    
    This endpoint allows creating notifications directly, which can be useful for 
    testing or special cases outside the normal reminder flow.
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
    Update a notification's sent_at or error_message.
    
    Note: Status changes should be made through dedicated endpoints:
    - /notifications/{id}/mark-as-sent
    - /notifications/{id}/mark-as-failed
    - /notifications/{id}/mark-as-cancelled
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
    Delete a notification.
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
    Resend a failed notification.
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
    Mark a notification as sent.
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
    Mark a notification as failed with an error message.
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
    Mark a notification as cancelled.
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
    Resend all failed notifications for the current user, up to the specified limit.
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
    [Admin Only] Retrieve notifications across all users with optional filtering.
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
    Generate pending notifications for a reminder without sending them.
    
    This is useful for preparing notifications in advance that will be sent later
    by scheduled jobs or manually by the user.
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
    Cancel all pending notifications for the current user, with optional filtering.
    
    You can filter by reminder_id or client_id to cancel only specific notifications.
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
    Delete multiple notifications for the current user, with optional filtering.
    
    You can filter by reminder_id, client_id, or status to delete only specific notifications.
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
    [Admin Only] Get global notification statistics.
    
    Returns counts by status, type, and delivery rates.
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
    [Admin Only] Delete failed notifications older than the specified days.
    
    This is useful for maintenance and cleanup of the notification table.
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
    [Admin Only] Resend all failed notifications across all users.
    
    This can be used to recover from system-wide notification failures.
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