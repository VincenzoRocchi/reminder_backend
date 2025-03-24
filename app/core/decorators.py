import functools
import logging
from app.core.settings import settings
from app.core.exceptions import InvalidConfigurationError, AppException

logger = logging.getLogger(__name__)

def validation_aware(validation_type: str = 'all'):
    """
    Decoratore che gestisce la logica di bypass delle validazioni in base alle impostazioni dell'ambiente.
    
    Args:
        validation_type: Tipo di validazione che questa funzione esegue
        
    Returns:
        Funzione decorata che rispetta le impostazioni di validazione
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Se non siamo in modalità di validazione rigorosa e questo è un errore di validazione
                if (not settings.should_validate(validation_type) and 
                    (isinstance(e, InvalidConfigurationError) or 
                     isinstance(e, ValueError) and "validation" in str(e).lower())):
                    
                    # Registra la validazione bypassata
                    logger.warning(
                        f"Validazione bypassata: {str(e)} | Funzione: {func.__name__} | "
                        f"STRICT_VALIDATION={settings.STRICT_VALIDATION}"
                    )
                    
                    # Per funzioni che modificano argomenti, potrebbe essere necessario restituire un valore di fallback
                    return kwargs.get('value', None)
                
                # Rilancia altre eccezioni o se la validazione rigorosa è abilitata
                raise
        return wrapper
    return decorator