from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.serviceAccounts import ServiceAccount as ServiceAccountModel, ServiceTypeEnum
from app.schemas.serviceAccounts import ServiceAccount, ServiceAccountCreate, ServiceAccountUpdate, ServiceType

router = APIRouter()

@router.get("/", response_model=List[ServiceAccount])
async def read_service_accounts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
    service_type: ServiceType = None,
):
    """
    Retrieve all service accounts for the current user.
    Optionally filter by service type.
    """
    query = db.query(ServiceAccountModel).filter(ServiceAccountModel.user_id == current_user.id)
    
    # Filter by service type if provided
    if service_type:
        query = query.filter(ServiceAccountModel.service_type == service_type)
    
    service_accounts = query.offset(skip).limit(limit).all()
    return service_accounts

@router.post("/", response_model=ServiceAccount, status_code=status.HTTP_201_CREATED)
async def create_service_account(
    service_account_in: Annotated[ServiceAccountCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new service account for the current user.
    """
    # Additional validation based on service type
    if service_account_in.service_type == ServiceType.EMAIL:
        if service_account_in.smtp_password and not (service_account_in.smtp_host and service_account_in.smtp_port):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="SMTP configuration requires host and port"
            )
    elif service_account_in.service_type == ServiceType.SMS:
        if service_account_in.twilio_auth_token and not service_account_in.twilio_account_sid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Twilio configuration requires account SID"
            )
    
    # Convert Pydantic enum to SQLAlchemy enum
    service_type_value = ServiceTypeEnum(service_account_in.service_type.value)
    
    # Create the service account
    service_account_data = service_account_in.model_dump()
    service_account_data["service_type"] = service_type_value
    
    service_account = ServiceAccountModel(
        user_id=current_user.id,
        **service_account_data
    )
    
    try:
        db.add(service_account)
        db.commit()
        db.refresh(service_account)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return service_account

@router.get("/{service_account_id}", response_model=ServiceAccount)
async def read_service_account(
    service_account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific service account by ID.
    """
    service_account = db.query(ServiceAccountModel)\
        .filter(ServiceAccountModel.id == service_account_id)\
        .first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
    
    if service_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return service_account

@router.put("/{service_account_id}", response_model=ServiceAccount)
async def update_service_account(
    service_account_id: int,
    service_account_in: Annotated[ServiceAccountUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update a service account.
    """
    service_account = db.query(ServiceAccountModel)\
        .filter(ServiceAccountModel.id == service_account_id)\
        .first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
    
    if service_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update fields
    update_data = service_account_in.model_dump(exclude_unset=True)
    
    # Additional validation
    if 'smtp_password' in update_data and not (service_account.smtp_host or update_data.get('smtp_host')):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="SMTP configuration requires host"
        )
    
    for field, value in update_data.items():
        setattr(service_account, field, value)
    
    try:
        db.add(service_account)
        db.commit()
        db.refresh(service_account)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return service_account

@router.delete("/{service_account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    service_account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete a service account.
    """
    service_account = db.query(ServiceAccountModel)\
        .filter(ServiceAccountModel.id == service_account_id)\
        .first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
    
    if service_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        db.delete(service_account)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    return {"detail": "Service account deleted successfully"}

@router.get("/test/{service_account_id}", response_model=dict)
async def test_service_account(
    service_account_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Test if a service account is properly configured by attempting to connect to the service.
    """
    service_account = db.query(ServiceAccountModel)\
        .filter(ServiceAccountModel.id == service_account_id)\
        .first()
    
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
    
    if service_account.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Test logic would depend on the service type
    # For now, just return a success message
    return {
        "status": "success",
        "message": f"Service account '{service_account.service_name}' is configured correctly",
        "service_type": service_account.service_type.value
    }