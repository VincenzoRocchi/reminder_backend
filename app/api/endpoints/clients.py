from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.schemas.clients import Client, ClientCreate, ClientUpdate, ClientDetail
from app.core.exceptions import DatabaseError, AppException
from app.services.client import client_service

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
    return client_service.get_clients_by_user_id(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search
    )

@router.post("/", response_model=Client, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: Annotated[ClientCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new client for the current user.
    """
    return client_service.create_client(
        db,
        client_in=client_in,
        user_id=current_user.id
    )

@router.get("/{client_id}", response_model=ClientDetail)
async def read_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific client by ID with additional statistics.
    """
    return client_service.get_client_with_stats(
        db,
        client_id=client_id,
        user_id=current_user.id
    )

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
    return client_service.update_client(
        db,
        client_id=client_id,
        user_id=current_user.id,
        client_in=client_in
    )

@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a client.
    """
    client_service.delete_client(
        db,
        client_id=client_id,
        user_id=current_user.id
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
            client_service.create_client(
                db,
                client_in=client_data,
                user_id=current_user.id
            )
            imported_count += 1
        except Exception as e:
            failed_imports.append({
                "data": client_data.model_dump(),
                "error": str(e)
            })
            
    return {
        "imported_count": imported_count,
        "failed_count": len(failed_imports),
        "failed_imports": failed_imports
    }