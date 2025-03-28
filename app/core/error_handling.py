import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from app.core.exceptions import AppException, DatabaseError

logger = logging.getLogger(__name__)

# Define type variables for the decorator
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

def handle_exceptions(
    error_message: str = "Operation failed",
    log_error: bool = True,
    reraise: bool = True
) -> Callable[[F], F]:
    """
    A decorator for standardized exception handling.
    
    Args:
        error_message: Base message to use when creating exception
        log_error: Whether to log the exception
        reraise: Whether to reraise the exception (True) or return None (False)
        
    Returns:
        Decorated function
        
    Example:
        @handle_exceptions(error_message="Failed to create user")
        def create_user(db, user_data):
            # function implementation
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except AppException:
                # If it's already an application exception, just re-raise it
                if log_error:
                    logger.exception(f"{error_message} - AppException caught")
                if reraise:
                    raise
                return None
            except Exception as e:
                if log_error:
                    logger.exception(f"{error_message}: {str(e)}")
                
                if reraise:
                    # Convert to a database error for database operations or 
                    # re-wrap in a more specific exception if needed
                    raise DatabaseError(f"{error_message}", str(e))
                return None
        return cast(F, wrapper)
    return decorator

def with_transaction(func: F) -> F:
    """
    A decorator to handle database transactions and rollbacks.
    
    This decorator wraps the function in a try/except block and performs
    rollback in case of exceptions.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
        
    Example:
        @with_transaction
        def create_user(db, user_data):
            # function implementation that uses db.commit()
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Find the database session argument
        db = None
        
        # Look for the db argument in args and kwargs
        for arg in args:
            if hasattr(arg, 'commit') and hasattr(arg, 'rollback'):
                db = arg
                break
        
        if not db and 'db' in kwargs:
            db = kwargs['db']
            
        if not db:
            # If we can't find db, just call the function normally
            return func(*args, **kwargs)
            
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            # Roll back the transaction if an exception occurs
            if db and hasattr(db, 'rollback'):
                db.rollback()
            raise
    return cast(F, wrapper) 