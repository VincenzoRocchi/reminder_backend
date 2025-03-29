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
    Retrieve all clients belonging to the current user.
    
    This endpoint:
    - Returns a list of all clients associated with the authenticated user
    - Supports pagination with skip and limit parameters
    - Provides optional search functionality to filter results by name or email
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    - search: Optional search term to filter clients by name or email
    
    Returns:
    - List of client objects with basic information
    
    Notes:
    - Results are sorted by name in ascending order
    - Only returns clients owned by the authenticated user
    - For detailed information about a specific client, use the GET /{client_id} endpoint
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
    
    This endpoint:
    - Creates a new client record associated with the authenticated user
    - Validates input data according to the ClientCreate schema
    - Returns the created client object with generated ID and timestamps
    
    Required fields:
    - name: Client's full name or company name (1-255 characters)
    
    Optional fields:
    - email: Client's email address for communications
    - phone_number: Client's phone number in international format
    - address: Client's physical address (max 500 characters)
    - notes: Additional information about the client
    - is_active: Whether the client is active (defaults to true)
    
    Notes:
    - The client is automatically associated with the authenticated user
    - Email addresses are validated for proper format
    - Phone numbers should be in international format (e.g., +1234567890)
    - For bulk imports, use the /bulk-import endpoint
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
    Get detailed information about a specific client by ID.
    
    This endpoint:
    - Retrieves complete information about a single client
    - Includes additional statistics (reminders count, notifications count)
    - Performs ownership validation to ensure the client belongs to the current user
    
    Parameters:
    - client_id: The unique identifier of the client to retrieve
    
    Returns:
    - Detailed client object with basic information and statistics
    
    Notes:
    - Returns 404 if the client doesn't exist
    - Returns 404 if the client doesn't belong to the authenticated user
    - Includes counts of associated reminders and notifications for reporting
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
    Update an existing client's information.
    
    This endpoint:
    - Updates specified fields for an existing client
    - Performs ownership validation to ensure the client belongs to the current user
    - Returns the updated client object
    
    Parameters:
    - client_id: The unique identifier of the client to update
    
    Available fields to update:
    - name: Client's updated name (1-255 characters)
    - email: Updated email address
    - phone_number: Updated phone number
    - address: Updated physical address
    - notes: Updated additional information
    - is_active: Updated status (set to false to archive)
    
    Notes:
    - All fields are optional - only specified fields will be updated
    - Returns 404 if the client doesn't exist or doesn't belong to the authenticated user
    - To archive a client, set is_active to false rather than deleting it
    - The updated_at timestamp is automatically refreshed
    """
    return client_service.update_client(
        db,
        client_id=client_id,
        user_id=current_user.id,
        client_in=client_in
    )

@router.delete("/{client_id}", status_code=status.HTTP_200_OK)
async def delete_client(
    client_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Permanently delete a client from the system.
    
    This endpoint:
    - Completely removes the client and all associated data from the database
    - Performs ownership validation to ensure the client belongs to the current user
    - Returns a confirmation message upon successful deletion
    
    Parameters:
    - client_id: The unique identifier of the client to delete
    
    Notes:
    - This is a destructive operation that cannot be undone
    - Consider using the update endpoint to set is_active=false instead of deletion
    - Associated data like reminders and notifications will be affected by this operation
    - Returns 404 if the client doesn't exist or doesn't belong to the authenticated user
    """
    client_service.delete_client(
        db,
        client_id=client_id,
        user_id=current_user.id
    )
    return {"detail": "Client deleted successfully"}

@router.post("/bulk-import", response_model=dict, status_code=status.HTTP_201_CREATED)
async def bulk_import_clients(
    clients: Annotated[List[ClientCreate], Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Import multiple clients in a single operation.
    
    This endpoint:
    - Creates multiple client records in a single API call
    - Attempts to create each client independently
    - Returns a summary of successful and failed imports
    - Continues processing even if some clients fail to import
    
    Required body:
    - A list of client objects following the ClientCreate schema
    
    Returns:
    - imported_count: Number of successfully imported clients
    - failed_count: Number of clients that failed to import
    - failed_imports: List of objects with the failed data and error details
    
    Notes:
    - Useful for migrating clients from another system
    - Each client is validated independently
    - Import continues even when some records fail validation
    - The operation is not atomic - successful imports are committed even if others fail
    - All clients are associated with the authenticated user
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