from typing import List, Annotated
from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.notifications import NotificationStatusEnum
from app.schemas.notifications import NotificationSchema, NotificationUpdate, NotificationDetail
from app.core.exceptions import AppException
from app.services.notification import notification_service

router = APIRouter()

@router.get("/", response_model=List[NotificationSchema])
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

    return notification_service.get_notifications(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        reminder_id=reminder_id,
        client_id=client_id,
        status=status_enum
    )

@router.get("/{notification_id}", response_model=NotificationDetail)
async def read_notification(
    notification_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific notification by ID.
    """
    return notification_service.get_notification_detail(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )

@router.put("/{notification_id}", response_model=NotificationSchema)
async def update_notification(
    notification_id: int,
    notification_in: Annotated[NotificationUpdate, Body],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a notification status, sent_at, or error_message.
    """
    return notification_service.update_notification(
        db,
        notification_id=notification_id,
        user_id=current_user.id,
        notification_in=notification_in
    )

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