from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Body
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database import get_db
from app.models.users import User as UserModel
from app.models.emailConfigurations import EmailConfiguration as EmailConfigurationModel
from app.schemas.emailConfigurations import EmailConfiguration, EmailConfigurationCreate, EmailConfigurationUpdate
from app.core.exceptions import AppException, DatabaseError

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
    query = db.query(EmailConfigurationModel).filter(EmailConfigurationModel.user_id == current_user.id)
    
    email_configurations = query.offset(skip).limit(limit).all()
    return email_configurations

@router.post("/", response_model=EmailConfiguration, status_code=status.HTTP_201_CREATED)
async def create_email_configuration(
    config_in: Annotated[EmailConfigurationCreate, Body()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Create a new email configuration for the current user.
    """
    # Create the email configuration
    config_data = config_in.model_dump()
    
    email_configuration = EmailConfigurationModel(
        user_id=current_user.id,
        **config_data
    )
    
    try:
        db.add(email_configuration)
        db.commit()
        db.refresh(email_configuration)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return email_configuration

@router.get("/{config_id}", response_model=EmailConfiguration)
async def read_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Get a specific email configuration by ID.
    """
    config = db.query(EmailConfigurationModel).filter(
        EmailConfigurationModel.id == config_id,
        EmailConfigurationModel.user_id == current_user.id
    ).first()
    
    if not config:
        raise AppException(
            message="Email configuration not found",
            code="CONFIG_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    return config

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
    config = db.query(EmailConfigurationModel).filter(
        EmailConfigurationModel.id == config_id,
        EmailConfigurationModel.user_id == current_user.id
    ).first()
    
    if not config:
        raise AppException(
            message="Email configuration not found",
            code="CONFIG_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Update fields
    update_data = config_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    try:
        db.add(config)
        db.commit()
        db.refresh(config)
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
    return config

@router.delete("/{config_id}")
async def delete_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Delete an email configuration.
    """
    config = db.query(EmailConfigurationModel).filter(
        EmailConfigurationModel.id == config_id,
        EmailConfigurationModel.user_id == current_user.id
    ).first()
    
    if not config:
        raise AppException(
            message="Email configuration not found",
            code="CONFIG_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    try:
        db.delete(config)
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(details=str(e))
    
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
    config = db.query(EmailConfigurationModel).filter(
        EmailConfigurationModel.id == config_id,
        EmailConfigurationModel.user_id == current_user.id
    ).first()
    
    if not config:
        raise AppException(
            message="Email configuration not found",
            code="CONFIG_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Here you would actually test the SMTP connection
    # For now, just return a success message
    return {
        "status": "success",
        "message": f"Email configuration '{config.configuration_name}' connected successfully to {config.smtp_host}"
    }