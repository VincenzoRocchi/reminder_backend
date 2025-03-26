from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.senderIdentities import SenderIdentity as SenderIdentityModel, IdentityTypeEnum
from app.schemas.senderIdentities import SenderIdentity, SenderIdentityCreate, SenderIdentityUpdate
from app.core.exceptions import AppException, DatabaseError

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
    query = db.query(SenderIdentityModel).filter(SenderIdentityModel.user_id == current_user.id)
    
    if identity_type:
        try:
            identity_type_enum = IdentityTypeEnum(identity_type)
            query = query.filter(SenderIdentityModel.identity_type == identity_type_enum)
        except ValueError:
            raise AppException(
                message=f"Invalid identity type: {identity_type}",
                code="INVALID_IDENTITY_TYPE",
                status_code=status.HTTP_400_BAD_REQUEST
            )
    
    identities = query.offset(skip).limit(limit).all()
    return identities

@router.post("/", response_model=SenderIdentity, status_code=status.HTTP_201_CREATED)
async def create_sender_identity(
    identity_in: Annotated[SenderIdentityCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new sender identity for the current user.
    """
    # Convert Pydantic enum to SQLAlchemy enum
    identity_type_value = IdentityTypeEnum(identity_in.identity_type.value)
    
    # If this is being set as default, unset any existing defaults of the same type
    if identity_in.is_default:
        existing_defaults = db.query(SenderIdentityModel).filter(
            SenderIdentityModel.user_id == current_user.id,
            SenderIdentityModel.identity_type == identity_type_value,
            SenderIdentityModel.is_default == True
        ).all()
        
        for default_identity in existing_defaults:
            default_identity.is_default = False
            db.add(default_identity)
    
    # Create the sender identity
    identity_data = identity_in.model_dump()
    identity_data["identity_type"] = identity_type_value
    
    sender_identity = SenderIdentityModel(
        user_id=current_user.id,
        is_verified=False,  # New identities start as unverified
        **identity_data
    )
    
    try:
        db.add(sender_identity)
        db.commit()
        db.refresh(sender_identity)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return sender_identity

@router.get("/{identity_id}", response_model=SenderIdentity)
async def read_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific sender identity by ID.
    """
    identity = db.query(SenderIdentityModel).filter(
        SenderIdentityModel.id == identity_id,
        SenderIdentityModel.user_id == current_user.id
    ).first()
    
    if not identity:
        raise AppException(
            message="Sender identity not found",
            code="IDENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return identity

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
    identity = db.query(SenderIdentityModel).filter(
        SenderIdentityModel.id == identity_id,
        SenderIdentityModel.user_id == current_user.id
    ).first()
    
    if not identity:
        raise AppException(
            message="Sender identity not found",
            code="IDENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # If setting as default, unset any existing defaults of the same type
    if identity_in.is_default:
        existing_defaults = db.query(SenderIdentityModel).filter(
            SenderIdentityModel.user_id == current_user.id,
            SenderIdentityModel.identity_type == identity.identity_type,
            SenderIdentityModel.is_default == True,
            SenderIdentityModel.id != identity_id
        ).all()
        
        for default_identity in existing_defaults:
            default_identity.is_default = False
            db.add(default_identity)
    
    # Update fields
    update_data = identity_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(identity, field, value)
    
    try:
        db.add(identity)
        db.commit()
        db.refresh(identity)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return identity

@router.delete("/{identity_id}")
async def delete_sender_identity(
    identity_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a sender identity.
    """
    identity = db.query(SenderIdentityModel).filter(
        SenderIdentityModel.id == identity_id,
        SenderIdentityModel.user_id == current_user.id
    ).first()
    
    if not identity:
        raise AppException(
            message="Sender identity not found",
            code="IDENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        db.delete(identity)
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
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
    identity = db.query(SenderIdentityModel).filter(
        SenderIdentityModel.id == identity_id,
        SenderIdentityModel.user_id == current_user.id
    ).first()
    
    if not identity:
        raise AppException(
            message="Sender identity not found",
            code="IDENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # In production, this would require actual verification
    # For now, just mark as verified
    identity.is_verified = True
    
    try:
        db.add(identity)
        db.commit()
        db.refresh(identity)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return identity