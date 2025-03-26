import logging
from typing import Callable, Any, Optional, Dict
from pydantic import field_validator, model_validator
from app.core.settings import settings
from app.core.exceptions import InvalidConfigurationError

# Initialize logger
logger = logging.getLogger(__name__)

# Decorator to create flexible field validators
def flexible_field_validator(field_name: str, validation_type: str = 'format'):
    def decorator(validation_func: Callable[[Any], Any]):
        @field_validator(field_name)
        def validated_field(cls, value: Any) -> Any:
            if value is None:
                return None
            
            try:
                # Attempt to validate the field value using the provided validation function
                return validation_func(value)
            except (InvalidConfigurationError, ValueError) as e:
                # If validation fails and strict validation is not required, log a warning and return the original value
                if not settings.should_validate(validation_type):
                    logger.warning(
                        f"Pydantic validation bypassed: {field_name} | {str(e)} | "
                        f"STRICT_VALIDATION={settings.STRICT_VALIDATION}"
                    )
                    return value
                # If strict validation is required, re-raise the exception
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