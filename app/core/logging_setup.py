import logging
import logging.config
import sys
import json
from typing import Dict, Any
from pathlib import Path

from app.core.settings import settings
from app.core.request_context import RequestContextLogFilter

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_record["request_id"] = record.request_id
            
        if hasattr(record, 'user_id'):
            log_record["user_id"] = record.user_id
            
        if hasattr(record, 'request_path'):
            log_record["path"] = record.request_path
            
        if hasattr(record, 'request_ip'):
            log_record["client_ip"] = record.request_ip
        
        # Add exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add custom properties if available
        if hasattr(record, "props"):
            log_record.update(record.props)
            
        return json.dumps(log_record)

def setup_logging() -> None:
    """
    Set up logging configuration based on the environment.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Console handler for all environments
    console_handler = {
        "level": log_level,
        "class": "logging.StreamHandler",
        "stream": sys.stdout,
        "filters": ["request_context"],
    }
    
    # Choose formatter based on environment
    if settings.ENV == "production":
        console_handler["formatter"] = "json"
    else:
        console_handler["formatter"] = "standard"
    
    # Configure file logging for production
    file_handler = {
        "level": logging.WARNING,
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "logs/app.log",
        "maxBytes": 10485760,  # 10 MB
        "backupCount": 5,
        "formatter": "json" if settings.ENV == "production" else "standard",
        "filters": ["request_context"],
    }
    
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    # Complete logging config
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "json": {
                "()": JSONFormatter
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(request_id)s): %(message)s"
            },
        },
        "filters": {
            "request_context": {
                "()": RequestContextLogFilter,
            }
        },
        "handlers": {
            "console": console_handler,
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": log_level,
            },
            "app": {
                "handlers": ["console"],
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": getattr(logging, settings.SERVER_LOG_LEVEL.upper(), logging.INFO),
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": logging.WARNING,
                "propagate": False,
            },
        },
    }
    
    # Add file handler in production
    if settings.ENV == "production":
        config["handlers"]["file"] = file_handler
        config["loggers"][""]["handlers"].append("file")
        config["loggers"]["app"]["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log configuration complete
    logger = logging.getLogger(__name__)
    logger.debug("Logging configuration complete")

# Add a convenience function to add structured data to log messages
def log_with_context(logger, level, msg, context=None, **kwargs):
    """
    Add structured context data to logs.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        msg: Log message
        context: Dict of context data to add to the log
        **kwargs: Additional log data
    """
    extra = {"props": {}}
    
    if context:
        extra["props"].update(context)
    
    if kwargs:
        extra["props"].update(kwargs)
    
    getattr(logger, level)(msg, extra=extra if extra["props"] else None) 