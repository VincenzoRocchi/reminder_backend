import logging
from typing import Callable, Any, Optional, Dict
from pydantic import field_validator, model_validator
from app.core.settings import settings
from app.core.exceptions import InvalidConfigurationError

logger = logging.getLogger(__name__)

def flexible_field_validator(field_name: str, validation_type: str = 'format'):
    def decorator(validation_func: Callable[[Any], Any]):
        @field_validator(field_name)
        def validated_field(cls, value: Any) -> Any:
            if value is None:
                return None
                
            try:
                return validation_func(value)
            except (InvalidConfigurationError, ValueError) as e:
                if not settings.should_validate(validation_type):
                    logger.warning(
                        f"Pydantic validation bypassed: {field_name} | {str(e)} | "
                        f"STRICT_VALIDATION={settings.STRICT_VALIDATION}"
                    )
                    return value
                raise
        
        return validated_field
    
    return decorator


def validate_twilio_token(token: str) -> str:
    if len(token) != 32 or not token.startswith('SK'):
        raise ValueError("Twilio token must be 32 characters and start with 'SK'")
    return token


def validate_smtp_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("SMTP password must be at least 8 characters")
    return password


def validate_whatsapp_api_key(key: str) -> str:
    if len(key) < 16:
        raise ValueError("WhatsApp API key must be at least 16 characters")
    return key