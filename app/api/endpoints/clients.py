from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.clients import Client as ClientModel
from app.models.reminderRecipient import ReminderRecipient
from app.models.reminders import Reminder
from app.schemas.clients import Client, ClientCreate, ClientUpdate, ClientDetail

router = APIRouter()

@router.get("/", response_model=List[Client])
async def read_clients(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    search: str = None,
):
    """
    Retrieve all clients for the current user.
    Optionally filter by search term in name or email.
    """
    query = db.query(ClientModel).filter(ClientModel.user_id == current_user.id)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (ClientModel.name.ilike(search_term)) | 
            (ClientModel.email.ilike(search_term))
        )
    
    clients = query.offset(skip).limit(limit).all()
    return clients

@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: Annotated[ClientCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new client for the current user.
    """
    client = ClientModel(
        user_id=current_user.id,
        **client_in.model_dump()
    )
    
    try:
        db.add(client)
        db.commit()
        db.refresh(client)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return client

@router.get("/{client_id}", response_model=ClientDetail)
async def read_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific client by ID with additional statistics.
    """
    client = db.query(ClientModel)\
        .filter(ClientModel.id == client_id, ClientModel.user_id == current_user.id)\
        .first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Count reminders and notifications for this client
    reminders_count = db.query(ReminderRecipient)\
        .join(Reminder)\
        .filter(
            ReminderRecipient.client_id == client_id,
            Reminder.user_id == current_user.id
        )\
        .count()
    
    active_reminders_count = db.query(ReminderRecipient)\
        .join(Reminder)\
        .filter(
            ReminderRecipient.client_id == client_id,
            Reminder.user_id == current_user.id,
            Reminder.is_active == True
        )\
        .count()
    
    # Get the notifications count (we'll import this in production)
    notifications_count = 0
    
    # Create detailed client response
    client_detail = ClientDetail(
        **client.__dict__,
        reminders_count=reminders_count,
        active_reminders_count=active_reminders_count,
        notifications_count=notifications_count,
    )
    
    return client_detail

@router.put("/{client_id}", response_model=Client)
async def update_client(
    client_id: int,
    client_in: Annotated[ClientUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a client.
    """
    client = db.query(ClientModel)\
        .filter(ClientModel.id == client_id, ClientModel.user_id == current_user.id)\
        .first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    try:
        db.add(client)
        db.commit()
        db.refresh(client)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a client.
    """
    client = db.query(ClientModel)\
        .filter(ClientModel.id == client_id, ClientModel.user_id == current_user.id)\
        .first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    try:
        db.delete(client)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return {"detail": "Client deleted successfully"}

@router.post("/bulk-import", response_model=dict)
async def bulk_import_clients(
    clients: Annotated[List[ClientCreate], Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Import multiple clients at once.
    """
    imported_count = 0
    failed_imports = []
    
    for client_data in clients:
        try:
            client = ClientModel(
                user_id=current_user.id,
                **client_data.model_dump()
            )
            db.add(client)
            db.flush()  # Flush to get the ID, but don't commit yet
            imported_count += 1
        except Exception as e:
            failed_imports.append({
                "data": client_data.model_dump(),
                "error": str(e)
            })
    
    # Only commit if at least one client was successfully imported
    if imported_count > 0:
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during commit: {str(e)}"
            )
    
    return {
        "imported_count": imported_count,
        "failed_count": len(failed_imports),
        "failed_imports": failed_imports
    }