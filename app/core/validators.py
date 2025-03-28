import logging
from typing import Callable, Any, Optional, Dict
from pydantic import field_validator, model_validator
from app.core.settings import settings
from app.core.exceptions import InvalidConfigurationError

# Initialize logger
logger = logging.getLogger(__name__)

# Decorator to create field validators
def flexible_field_validator(field_name: str, validation_type: str = 'format'):
    def decorator(validation_func: Callable[[Any], Any]):
        @field_validator(field_name)
        def validated_field(cls, value: Any) -> Any:
            if value is None:
                return None
            
            try:
                # Validate the field value using the provided validation function
                return validation_func(value)
            except (InvalidConfigurationError, ValueError) as e:
                # All validation errors are now raised as strict validation is always enabled
                logger.warning(f"Validation failed: {field_name} | {str(e)}")
                raise
        
        return validated_field
    
    return decorator

# Validation function for Twilio token
def validate_twilio_token(token: str) -> str:
    if len(token) != 32 or not token.startswith('SK'):
        raise ValueError("Twilio token must be 32 characters and start with 'SK'")
    return token

# Validation function for SMTP password
def validate_smtp_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("SMTP password must be at least 8 characters")
    return password