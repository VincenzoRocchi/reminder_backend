from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db_session as get_db
from app.models.users import User as UserModel
from app.schemas.emailConfigurations import EmailConfiguration, EmailConfigurationCreate, EmailConfigurationUpdate
from app.core.exceptions import AppException
from app.services.emailConfiguration import email_configuration_service

router = APIRouter()

@router.get("/", response_model=List[EmailConfiguration])
async def read_email_configurations(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0,
    limit: int = 100,
):
    """
    Retrieve all email configurations for the current user.
    """
    return email_configuration_service.get_email_configurations_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.post("/", response_model=EmailConfiguration, status_code=status.HTTP_201_CREATED)
async def create_email_configuration(
    config_in: Annotated[EmailConfigurationCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new email configuration for the current user.
    """
    return email_configuration_service.create_email_configuration(
        db,
        obj_in=config_in,
        user_id=current_user.id
    )

@router.get("/{config_id}", response_model=EmailConfiguration)
async def read_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific email configuration by ID.
    """
    return email_configuration_service.get_email_configuration_by_user(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id
    )

@router.put("/{config_id}", response_model=EmailConfiguration)
async def update_email_configuration(
    config_id: int,
    config_in: Annotated[EmailConfigurationUpdate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Update an email configuration.
    """
    return email_configuration_service.update_email_configuration(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id,
        obj_in=config_in
    )

@router.delete("/{config_id}")
async def delete_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete an email configuration.
    """
    email_configuration_service.delete_email_configuration(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id
    )
    return {"detail": "Email configuration deleted successfully"}

@router.post("/{config_id}/test", response_model=dict)
async def test_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Test if an email configuration is properly configured by attempting to connect to the SMTP server.
    """
    config = email_configuration_service.test_email_configuration(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id
    )
    
    return {
        "status": "success",
        "message": f"Email configuration '{config.configuration_name}' connected successfully to {config.smtp_host}"
    }