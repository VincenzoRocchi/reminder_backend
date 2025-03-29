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
    Retrieve all email configurations belonging to the current user.
    
    This endpoint:
    - Returns a list of all email configurations created by the authenticated user
    - Supports pagination with skip and limit parameters
    - Excludes sensitive information like SMTP passwords from the response
    
    Parameters:
    - skip: Number of records to skip (for pagination)
    - limit: Maximum number of records to return (default 100)
    
    Returns:
    - List of email configuration objects with connection details and settings
    
    Notes:
    - Results are sorted by creation date in descending order (newest first)
    - Only returns configurations owned by the authenticated user
    - For detailed information about a specific configuration, use the GET /{config_id} endpoint
    - SMTP passwords are never returned in the response for security reasons
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
    Create a new email configuration for sending email notifications.
    
    This endpoint:
    - Creates a new email configuration record associated with the authenticated user
    - Securely stores SMTP connection details and credentials
    - Returns the created configuration (excluding password)
    
    Required fields:
    - configuration_name: Friendly name for this email configuration
    - smtp_host: SMTP server hostname (e.g., "smtp.gmail.com")
    - smtp_port: SMTP server port number (typically 25, 465, or 587)
    - smtp_user: SMTP username for authentication
    - smtp_password: SMTP password for authentication (stored securely, never returned in responses)
    - email_from: Email address that will appear as the sender
    
    Optional fields:
    - is_active: Whether this configuration is active and available for use (defaults to true)
    
    Returns:
    - Created email configuration object (without SMTP password)
    
    Notes:
    - The system doesn't verify SMTP connectivity during creation
    - Use the /{config_id}/test endpoint to verify proper configuration
    - For Gmail and other providers requiring OAuth2, you may need app-specific passwords
    - SMTP passwords are stored securely and never returned in API responses
    - Each user can have multiple email configurations for different purposes
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
    Get detailed information about a specific email configuration by ID.
    
    This endpoint:
    - Retrieves complete information about a single email configuration
    - Performs ownership validation to ensure the configuration belongs to the current user
    - Returns the configuration details (excluding the SMTP password)
    
    Parameters:
    - config_id: The unique identifier of the email configuration to retrieve
    
    Returns:
    - Email configuration object with connection details and settings (without password)
    
    Notes:
    - Returns 404 if the configuration doesn't exist
    - Returns 404 if the configuration doesn't belong to the authenticated user
    - SMTP passwords are never returned in the response for security reasons
    - To test if the configuration works correctly, use the /{config_id}/test endpoint
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
    Update an existing email configuration's settings.
    
    This endpoint:
    - Updates specified fields for an existing email configuration
    - Performs ownership validation to ensure the configuration belongs to the current user
    - Returns the updated configuration (excluding password)
    
    Parameters:
    - config_id: The unique identifier of the email configuration to update
    
    Available fields to update:
    - configuration_name: New friendly name for this configuration
    - smtp_host: New SMTP server hostname
    - smtp_port: New SMTP server port number
    - smtp_user: New SMTP username for authentication
    - smtp_password: New SMTP password for authentication
    - email_from: New sender email address
    - is_active: Updated active status (set to false to disable this configuration)
    
    Returns:
    - Updated email configuration object (without SMTP password)
    
    Notes:
    - All fields are optional - only specified fields will be updated
    - The SMTP password will only be updated if explicitly provided
    - If you don't provide the password field, the existing password will be retained
    - After updating connection details, use the /{config_id}/test endpoint to verify
    - Returns 404 if the configuration doesn't exist or doesn't belong to the authenticated user
    - Changing a configuration to inactive (is_active=false) will prevent it from being used for reminders
    """
    return email_configuration_service.update_email_configuration(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id,
        obj_in=config_in
    )

@router.delete("/{config_id}", status_code=status.HTTP_200_OK)
async def delete_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Permanently delete an email configuration from the system.
    
    This endpoint:
    - Completely removes the email configuration from the database
    - Performs ownership validation to ensure the configuration belongs to the current user
    - Returns a confirmation message upon successful deletion
    
    Parameters:
    - config_id: The unique identifier of the email configuration to delete
    
    Notes:
    - This is a destructive operation that cannot be undone
    - If the configuration is in use by any sender identities, deletion may fail
    - Consider using the update endpoint to set is_active=false instead of deletion
    - Returns 404 if the configuration doesn't exist or doesn't belong to the authenticated user
    """
    email_configuration_service.delete_email_configuration(
        db,
        email_configuration_id=config_id,
        user_id=current_user.id
    )
    return {"detail": "Email configuration deleted successfully"}

@router.post("/{config_id}/test", response_model=dict, status_code=status.HTTP_200_OK)
async def test_email_configuration(
    config_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
):
    """
    Test if an email configuration can successfully connect to the SMTP server.
    
    This endpoint:
    - Attempts to establish a connection to the configured SMTP server
    - Validates credentials and connection settings
    - Performs ownership validation to ensure the configuration belongs to the current user
    - Returns a success or error message based on the connection result
    
    Parameters:
    - config_id: The unique identifier of the email configuration to test
    
    Returns:
    - status: Operation result (success or error)
    - message: Description of the test result with connection details
    
    Notes:
    - This endpoint only tests connectivity and authentication
    - It does not actually send a test email
    - Connection timeouts are limited to prevent long-running requests
    - Common errors include incorrect hostname, blocked ports, or invalid credentials
    - For Gmail and similar services, you may need to allow "less secure apps" or use app passwords
    - Returns 404 if the configuration doesn't exist or doesn't belong to the authenticated user
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