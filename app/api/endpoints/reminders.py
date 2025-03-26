from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.reminders import Reminder as ReminderModel, NotificationTypeEnum
from app.models.serviceAccounts import ServiceAccount as ServiceAccountModel
from app.models.clients import Client as ClientModel
from app.models.reminderRecipient import ReminderRecipient
from app.schemas.reminders import Reminder, ReminderCreate, ReminderUpdate, ReminderDetail
from app.core.exceptions import AppException, DatabaseError

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
    query = db.query(ReminderModel).filter(ReminderModel.user_id == current_user.id)
    
    # Filter by active status if requested
    if active_only:
        query = query.filter(ReminderModel.is_active == True)
    
    # Filter by service account if provided
    if service_account_id:
        query = query.filter(ReminderModel.service_account_id == service_account_id)
    
    reminders = query.order_by(ReminderModel.reminder_date.desc()).offset(skip).limit(limit).all()
    return reminders

@router.post("/", response_model=ReminderDetail, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    reminder_in: Annotated[ReminderCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new reminder with client associations.
    """
    # Verify service account belongs to user
    if reminder_in.service_account_id:
        service_account = db.query(ServiceAccountModel).filter(
            ServiceAccountModel.id == reminder_in.service_account_id,
            ServiceAccountModel.user_id == current_user.id
        ).first()
        
        if not service_account:
            raise AppException(
                message="Service account not found or not owned by user",
                code="SERVICE_ACCOUNT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check that service type matches notification type
        if service_account.service_type.value != reminder_in.notification_type.value:
            raise AppException(
                message=f"Service account type ({service_account.service_type.value}) doesn't match notification type ({reminder_in.notification_type.value})",
                code="SERVICE_TYPE_MISMATCH",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # Verify clients exist and belong to user
    client_ids = reminder_in.client_ids
    if client_ids:
        clients = db.query(ClientModel).filter(
            ClientModel.id.in_(client_ids),
            ClientModel.user_id == current_user.id
        ).all()
        
        found_client_ids = [client.id for client in clients]
        missing_client_ids = set(client_ids) - set(found_client_ids)
        
        if missing_client_ids:
            raise AppException(
                message=f"Clients not found or not owned by user: {missing_client_ids}",
                code="CLIENT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
    
    # Create reminder
    reminder_data = reminder_in.model_dump(exclude={"client_ids"})
    reminder = ReminderModel(
        user_id=current_user.id,
        **reminder_data
    )
    
    try:
        db.add(reminder)
        db.flush()  # Get the ID without committing
        
        # Create client associations
        for client_id in client_ids:
            recipient = ReminderRecipient(
                reminder_id=reminder.id,
                client_id=client_id
            )
            db.add(recipient)
        
        db.commit()
        db.refresh(reminder)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e)) 
    
    # Get client IDs for response
    reminder_recipients = db.query(ReminderRecipient).filter(
        ReminderRecipient.reminder_id == reminder.id
    ).all()
    
    client_ids = [recipient.client_id for recipient in reminder_recipients]
    
    # Create detailed response
    reminder_detail = ReminderDetail(
        **reminder.__dict__,
        clients=client_ids
    )
    
    return reminder_detail

@router.get("/{reminder_id}", response_model=ReminderDetail)
async def read_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific reminder by ID with client details.
    """
    reminder = db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise AppException(
            message="Reminder not found",
            code="REMINDER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Get client IDs
    reminder_recipients = db.query(ReminderRecipient).filter(
        ReminderRecipient.reminder_id == reminder.id
    ).all()
    
    client_ids = [recipient.client_id for recipient in reminder_recipients]
    
    # Get notification counts (we'll implement this in production)
    notifications_count = 0
    sent_count = 0
    failed_count = 0
    
    # Create detailed response
    reminder_detail = ReminderDetail(
        **reminder.__dict__,
        clients=client_ids,
        notifications_count=notifications_count,
        sent_count=sent_count,
        failed_count=failed_count
    )
    
    return reminder_detail

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
    reminder = db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise AppException(
            message="Reminder not found",
            code="REMINDER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Verify service account if being updated
    if reminder_in.service_account_id is not None:
        service_account = db.query(ServiceAccountModel).filter(
            ServiceAccountModel.id == reminder_in.service_account_id,
            ServiceAccountModel.user_id == current_user.id
        ).first()
        
        if not service_account:
            raise AppException(
                message="Service account not found or not owned by user",
                code="SERVICE_ACCOUNT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        # If notification type is being updated, check compatibility
        notification_type = reminder_in.notification_type or reminder.notification_type
        if service_account.service_type.value != notification_type.value:
            raise AppException(
                message=f"Service account type ({service_account.service_type.value}) doesn't match notification type ({notification_type.value})",
                code="SERVICE_TYPE_MISMATCH",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    # Update reminder fields
    update_data = reminder_in.model_dump(exclude={"client_ids"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(reminder, field, value)
    
    try:
        # Update client associations if provided
        if reminder_in.client_ids is not None:
            # Verify clients exist and belong to user
            client_ids = reminder_in.client_ids
            if client_ids:
                clients = db.query(ClientModel).filter(
                    ClientModel.id.in_(client_ids),
                    ClientModel.user_id == current_user.id
                ).all()
                
                found_client_ids = [client.id for client in clients]
                missing_client_ids = set(client_ids) - set(found_client_ids)
                
                if missing_client_ids:
                    raise AppException(
                        message=f"Clients not found or not owned by user: {missing_client_ids}",
                        code="CLIENT_NOT_FOUND",
                        status_code=status.HTTP_404_NOT_FOUND
                    )
            
            # Delete existing associations
            db.query(ReminderRecipient).filter(
                ReminderRecipient.reminder_id == reminder.id
            ).delete()
            
            # Create new associations
            for client_id in client_ids:
                recipient = ReminderRecipient(
                    reminder_id=reminder.id,
                    client_id=client_id
                )
                db.add(recipient)
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
        
    # Get updated client IDs
    reminder_recipients = db.query(ReminderRecipient).filter(
        ReminderRecipient.reminder_id == reminder.id
    ).all()
    
    client_ids = [recipient.client_id for recipient in reminder_recipients]
    
    # Create detailed response
    reminder_detail = ReminderDetail(
        **reminder.__dict__,
        clients=client_ids
    )
    
    return reminder_detail

@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a reminder.
    """
    reminder = db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise AppException(
            message="Reminder not found",
            code="REMINDER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        db.delete(reminder)
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return {"detail": "Reminder deleted successfully"}

@router.post("/{reminder_id}/send-now", response_model=dict)
async def send_reminder_now(
    reminder_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Trigger a reminder to send immediately, regardless of scheduled date.
    """
    reminder = db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == current_user.id
    ).first()
    
    if not reminder:
        raise AppException(
            message="Reminder not found",
            code="REMINDER_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # For now, just return a success message
    # In production, this would call the scheduler service
    return {
        "status": "success",
        "message": f"Reminder '{reminder.title}' queued for immediate delivery",
        "timestamp": datetime.now().isoformat()
    }