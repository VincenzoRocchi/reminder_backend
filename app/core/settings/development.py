# app/core/settings/development.py
import os
import secrets
from .base import BaseAppSettings
from pydantic import field_validator, Field, computed_field
import re

class DevelopmentSettings(BaseAppSettings):
    # Class variable to store the generated key
    _dev_secret_key: str = None
    
    # Use computed_field to provide a development-specific secret key
    @computed_field
    def DEV_SECRET_KEY(self) -> str:
        # Use the environment variable if set
        env_key = os.getenv("DEV_SECRET_KEY")
        if env_key:
            return env_key
            
        # Otherwise use a generated key that persists for the app's lifetime
        if DevelopmentSettings._dev_secret_key is None:
            DevelopmentSettings._dev_secret_key = secrets.token_urlsafe(32)
            print("WARNING: Using a generated DEV_SECRET_KEY. For consistent sessions across restarts, set DEV_SECRET_KEY environment variable.")
        
        return DevelopmentSettings._dev_secret_key
    
    @field_validator('STRICT_VALIDATION')
    def validate_strict_validation(cls, v):
        if v is True:
            raise ValueError(
                "STRICT_VALIDATION must be False in development environment. "
                "If you need strict validation, use the testing environment instead "
                "by setting ENV=testing."
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
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if not v:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.development file."
            )
        
        if v and 'sqlite' in v.lower():
            raise ValueError("Development must use a real database, not SQLite")
        return v