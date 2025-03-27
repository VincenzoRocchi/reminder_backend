import contextvars
import logging
import uuid
from typing import Dict, Any, Optional

# Context variables for request tracking
request_id_var = contextvars.ContextVar('request_id', default=None)
user_id_var = contextvars.ContextVar('user_id', default=None)
request_path_var = contextvars.ContextVar('request_path', default=None)
request_ip_var = contextvars.ContextVar('request_ip', default=None)
extra_context_var = contextvars.ContextVar('extra_context', default={})

logger = logging.getLogger(__name__)

def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()

def set_request_id(request_id: Optional[str] = None) -> None:
    """Set the current request ID."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)

def get_user_id() -> Optional[int]:
    """Get the current user ID."""
    return user_id_var.get()

def set_user_id(user_id: Optional[int]) -> None:
    """Set the current user ID."""
    user_id_var.set(user_id)

def get_request_path() -> Optional[str]:
    """Get the current request path."""
    return request_path_var.get()

def set_request_path(path: Optional[str]) -> None:
    """Set the current request path."""
    request_path_var.set(path)

def get_request_ip() -> Optional[str]:
    """Get the client IP for the current request."""
    return request_ip_var.get()

def set_request_ip(ip: Optional[str]) -> None:
    """Set the client IP for the current request."""
    request_ip_var.set(ip)

def get_context_value(key: str) -> Any:
    """Get a value from the current request context."""
    context = extra_context_var.get()
    return context.get(key)

def set_context_value(key: str, value: Any) -> None:
    """Set a value in the current request context."""
    context = extra_context_var.get().copy()
    context[key] = value
    extra_context_var.set(context)

def get_all_context() -> Dict[str, Any]:
    """Get all the context information for the current request."""
    context = {
        'request_id': get_request_id(),
        'user_id': get_user_id(),
        'request_path': get_request_path(),
        'request_ip': get_request_ip(),
    }
    
    # Add extra context
    extra = extra_context_var.get()
    if extra:
        context.update(extra)
        
    return context

def clear_context() -> None:
    """Clear all context variables for the current request."""
    request_id_var.set(None)
    user_id_var.set(None)
    request_path_var.set(None)
    request_ip_var.set(None)
    extra_context_var.set({})

class RequestContextLogFilter(logging.Filter):
    """Log filter that adds request context to log records."""
    
    def filter(self, record):
        """Add request context to log record."""
        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            record.request_id = request_id
            
        # Add user ID if available
        user_id = get_user_id()
        if user_id:
            record.user_id = user_id
            
        # Add request path if available
        request_path = get_request_path()
        if request_path:
            record.request_path = request_path
            
        # Add request IP if available
        request_ip = get_request_ip()
        if request_ip:
            record.request_ip = request_ip
            
        # Add all extra context if available
        extra = extra_context_var.get()
        if extra:
            if not hasattr(record, 'props'):
                record.props = {}
            record.props.update(extra)
            
        return True 