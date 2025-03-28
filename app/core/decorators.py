import functools
import logging
from app.core.settings import settings
from app.core.exceptions import InvalidConfigurationError, AppException

logger = logging.getLogger(__name__)

def validation_aware(validation_type: str = 'all'):
    """
    Decorator that handles validation bypass logic based on environment settings.
    
    Args:
        validation_type: Type of validation this function performs
        
    Returns:
        Decorated function that respects validation settings
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # If we're not in strict validation mode and this is a validation error
                if (not settings.should_validate(validation_type) and 
                    (isinstance(e, InvalidConfigurationError) or 
                     isinstance(e, ValueError) and "validation" in str(e).lower())):
                    
                    # Log the bypassed validation
                    logger.warning(
                        f"Validation bypassed: {str(e)} | Function: {func.__name__} | "
                        f"STRICT_VALIDATION={settings.STRICT_VALIDATION}"
                    )
                    
                    # For functions that modify arguments, it might be necessary to return a fallback value
                    return kwargs.get('value', None)
                
                # Re-raise other exceptions or if strict validation is enabled
                raise
        return wrapper
    return decorator