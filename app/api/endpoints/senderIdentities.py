from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.models.senderIdentities import IdentityTypeEnum
from app.schemas.senderIdentities import (
    SenderIdentity, 
    SenderIdentityCreate, 
    SenderIdentityUpdate,
    EmailSenderIdentityCreate,
    EmailSenderIdentityUpdate,
    PhoneSenderIdentityCreate,
    PhoneSenderIdentityUpdate
)
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
    
    Note: For a more streamlined API, consider using the type-specific endpoints:
    - POST /sender-identities/email
    - POST /sender-identities/phone
    """
    return sender_identity_service.create_sender_identity(
        db,
        obj_in=identity_in,
        user_id=current_user.id
    )

@router.post("/email", response_model=SenderIdentity, status_code=status.HTTP_201_CREATED)
async def create_email_sender_identity(
    identity_in: Annotated[EmailSenderIdentityCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new email sender identity for the current user.
    
    This endpoint provides a simplified interface for creating email identities:
    - No need to specify identity_type (automatically set to EMAIL)
    - Only relevant fields for email identities are required
    
    Required fields:
    - email: The email address for this identity
    - display_name: Name shown to recipients
    - email_configuration_id: ID of an existing email configuration
    
    Optional fields:
    - is_default: Whether this should be the default email identity
    """
    # Convert the email-specific schema to the generic schema
    generic_data = {
        "identity_type": IdentityTypeEnum.EMAIL,
        "email": identity_in.email,
        "display_name": identity_in.display_name,
        "email_configuration_id": identity_in.email_configuration_id,
        "is_default": identity_in.is_default
    }
    
    return sender_identity_service.create_sender_identity(
        db,
        obj_in=generic_data,
        user_id=current_user.id
    )

@router.post("/phone", response_model=SenderIdentity, status_code=status.HTTP_201_CREATED)
async def create_phone_sender_identity(
    identity_in: Annotated[PhoneSenderIdentityCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new phone sender identity for the current user.
    
    This endpoint provides a simplified interface for creating phone identities:
    - No need to specify identity_type (automatically set to PHONE)
    - Only relevant fields for phone identities are required
    
    Required fields:
    - phone_number: Phone number in international format (e.g., +1234567890)
    - display_name: Name shown to recipients
    
    Optional fields:
    - is_default: Whether this should be the default phone identity
    """
    # Convert the phone-specific schema to the generic schema
    generic_data = {
        "identity_type": IdentityTypeEnum.PHONE,
        "phone_number": identity_in.phone_number,
        "display_name": identity_in.display_name,
        "is_default": identity_in.is_default
    }
    
    return sender_identity_service.create_sender_identity(
        db,
        obj_in=generic_data,
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
    
    Note: For a more streamlined API, consider using the type-specific endpoints:
    - PUT /sender-identities/{identity_id}/email
    - PUT /sender-identities/{identity_id}/phone
    """
    return sender_identity_service.update_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id,
        obj_in=identity_in
    )

@router.put("/{identity_id}/email", response_model=SenderIdentity)
async def update_email_sender_identity(
    identity_id: int,
    identity_in: Annotated[EmailSenderIdentityUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update an email sender identity.
    
    This endpoint provides a simplified interface for updating email identities:
    - Only relevant fields for email identities are available
    - Cannot change the identity type (use the generic endpoint for that)
    
    Available fields to update:
    - email: The email address
    - display_name: Name shown to recipients
    - email_configuration_id: ID of an email configuration
    - is_default: Whether this should be the default email identity
    """
    # First, verify this is an email identity
    identity = sender_identity_service.get_sender_identity(
        db, sender_identity_id=identity_id, user_id=current_user.id
    )
    
    if identity.identity_type != IdentityTypeEnum.EMAIL:
        raise AppException(
            message=f"Cannot update identity with ID {identity_id} as email identity: it is a {identity.identity_type} identity",
            code="IDENTITY_TYPE_MISMATCH",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Convert the email-specific update schema to the generic update schema
    update_data = {}
    if identity_in.email is not None:
        update_data["email"] = identity_in.email
    if identity_in.display_name is not None:
        update_data["display_name"] = identity_in.display_name
    if identity_in.email_configuration_id is not None:
        update_data["email_configuration_id"] = identity_in.email_configuration_id
    if identity_in.is_default is not None:
        update_data["is_default"] = identity_in.is_default
    
    return sender_identity_service.update_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id,
        obj_in=update_data
    )

@router.put("/{identity_id}/phone", response_model=SenderIdentity)
async def update_phone_sender_identity(
    identity_id: int,
    identity_in: Annotated[PhoneSenderIdentityUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a phone sender identity.
    
    This endpoint provides a simplified interface for updating phone identities:
    - Only relevant fields for phone identities are available
    - Cannot change the identity type (use the generic endpoint for that)
    
    Available fields to update:
    - phone_number: Phone number in international format
    - display_name: Name shown to recipients
    - is_default: Whether this should be the default phone identity
    """
    # First, verify this is a phone identity
    identity = sender_identity_service.get_sender_identity(
        db, sender_identity_id=identity_id, user_id=current_user.id
    )
    
    if identity.identity_type != IdentityTypeEnum.PHONE:
        raise AppException(
            message=f"Cannot update identity with ID {identity_id} as phone identity: it is a {identity.identity_type} identity",
            code="IDENTITY_TYPE_MISMATCH",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Convert the phone-specific update schema to the generic update schema
    update_data = {}
    if identity_in.phone_number is not None:
        update_data["phone_number"] = identity_in.phone_number
    if identity_in.display_name is not None:
        update_data["display_name"] = identity_in.display_name
    if identity_in.is_default is not None:
        update_data["is_default"] = identity_in.is_default
    
    return sender_identity_service.update_sender_identity(
        db,
        sender_identity_id=identity_id,
        user_id=current_user.id,
        obj_in=update_data
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

@router.get("/email", response_model=List[SenderIdentity])
async def read_email_sender_identities(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all email sender identities for the current user.
    """
    return sender_identity_service.get_user_sender_identities(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        identity_type=IdentityTypeEnum.EMAIL
    )

@router.get("/phone", response_model=List[SenderIdentity])
async def read_phone_sender_identities(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all phone sender identities for the current user.
    """
    return sender_identity_service.get_user_sender_identities(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        identity_type=IdentityTypeEnum.PHONE
    )