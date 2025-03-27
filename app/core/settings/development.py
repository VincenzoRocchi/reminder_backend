# app/core/settings/development.py
import os
import secrets
from .base import BaseAppSettings
from pydantic import field_validator, Field, computed_field
import re
import logging

logger = logging.getLogger(__name__)

class DevelopmentSettings(BaseAppSettings):
    # Class variable to store the generated key
    _dev_secret_key: str = None
    
    # Use computed_field to provide a development-specific secret key
    @computed_field
    def DEV_SECRET_KEY(self) -> str:
        # First try from environment variable
        env_key = os.getenv("DEV_SECRET_KEY")
        if env_key:
            return env_key
        
        # If not found, use cached or generate a new key
        if DevelopmentSettings._dev_secret_key is None:
            DevelopmentSettings._dev_secret_key = secrets.token_urlsafe(32)
            logger.warning("Using a generated DEV_SECRET_KEY. For consistent sessions across restarts, set DEV_SECRET_KEY environment variable.")
        
        return DevelopmentSettings._dev_secret_key
    
    # Updated to log a warning instead of raising an error if STRICT_VALIDATION=True
    @field_validator('STRICT_VALIDATION')
    def validate_strict_validation(cls, v):
        # Log warning if STRICT_VALIDATION=True in development
        if v is True:
            logger.warning(
                "STRICT_VALIDATION is set to True in development environment. "
                "This might make debugging more difficult as validation errors will cause exceptions instead of warnings. "
                "Consider setting STRICT_VALIDATION=False for easier debugging if needed."
            )
        return v
    
    # Validate that we're using DEBUG or INFO log level in development
    @field_validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        if v.upper() not in ["DEBUG", "INFO"]:
            raise ValueError(
                "LOG_LEVEL should be set to DEBUG or INFO in development environment. "
                "For a better development experience, DEBUG is recommended. "
                "For other log levels, use the testing environment by setting ENV=testing."
            )
        return v
    
    # Validate that we're using a real database in development
    @field_validator('DB_ENGINE')
    def validate_db_engine(cls, v):
        if v == 'sqlite':
            raise ValueError(
                "Development must use a proper database engine, (mysql+pymysql, postgresql), not SQLite. "
                "SQLite is only for testing environment."
            )
        return v
    
    # Validate database URI if explicitly provided
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if not v:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.development file."
            )
        return v 