from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.senderIdentities import IdentityTypeEnum
from app.schemas.senderIdentities import SenderIdentity, SenderIdentityCreate, SenderIdentityUpdate
from app.core.exceptions import AppException
from app.services.senderIdentity import sender_identity_service

router = APIRouter()

@router.get("/", response_model=List[SenderIdentity])
async def read_sender_identities(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    identity_type: str = None,
):
    """
    Retrieve all sender identities for the current user.
    Optionally filter by identity type.
    """
    if identity_type:
        try:
            identity_type_enum = IdentityTypeEnum(identity_type)
        except ValueError:
            raise AppException(
                message=f"Invalid identity type: {identity_type}",
                code="INVALID_IDENTITY_TYPE",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    else:
        identity_type_enum = None

    return sender_identity_service.get_user_sender_identities(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        identity_type=identity_type_enum
    )

@router.post("/", response_model=SenderIdentity, status_code=status.HTTP_201_CREATED)
async def create_sender_identity(
    identity_in: Annotated[SenderIdentityCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new sender identity for the current user.
    """
    return sender_identity_service.create_sender_identity(
        db,
        obj_in=identity_in,
        user_id=current_user.id
    )

@router.get("/{identity_id}", response_model=SenderIdentity)
async def read_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific sender identity by ID.
    """
    return sender_identity_service.get_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id
    )

@router.put("/{identity_id}", response_model=SenderIdentity)
async def update_sender_identity(
    identity_id: int,
    identity_in: Annotated[SenderIdentityUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a sender identity.
    """
    return sender_identity_service.update_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id,
        obj_in=identity_in
    )

@router.delete("/{identity_id}")
async def delete_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a sender identity.
    """
    sender_identity_service.delete_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id
    )
    return {"detail": "Sender identity deleted successfully"}

@router.post("/{identity_id}/verify", response_model=SenderIdentity)
async def verify_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Mark a sender identity as verified.
    In a real implementation, this would involve sending a verification code
    and verifying that the user owns the phone number or email.
    """
    return sender_identity_service.verify_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id
    )

@router.post("/{identity_id}/set-default", response_model=SenderIdentity)
async def set_default_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Set a sender identity as the default for its type.
    This will unset any other identity of the same type as default.
    """
    return sender_identity_service.set_default_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id
    )