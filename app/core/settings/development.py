# app/core/settings/development.py
import os
import secrets
from .base import BaseAppSettings
from pydantic import field_validator
import re

class DevelopmentSettings(BaseAppSettings):
    # Critical development overrides
    STRICT_VALIDATION: bool = False
    
    # Get SECRET_KEY from environment or generate a random one
    # that persists for the lifetime of the application
    _dev_secret_key: str = None
    
    @property
    def SECRET_KEY(self) -> str:
        # Use the environment variable if set
        env_key = os.getenv("DEV_SECRET_KEY")
        if env_key:
            return env_key
            
        # Otherwise use a generated key that persists for the app's lifetime
        if DevelopmentSettings._dev_secret_key is None:
            DevelopmentSettings._dev_secret_key = secrets.token_urlsafe(32)
            print("WARNING: Using a generated SECRET_KEY. For consistent sessions across restarts, set DEV_SECRET_KEY environment variable.")
        
        return DevelopmentSettings._dev_secret_key
    
    # Validate that we're using a real database in development
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if v and 'sqlite' in v.lower():
            raise ValueError("Development must use a real database, not SQLite")
        return v
    
    def model_post_init(self, **kwargs):
        super().model_post_init(**kwargs)
        
        # Ensure we have a database connection
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.development file."
            )