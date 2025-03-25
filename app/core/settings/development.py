# app/core/settings/development.py
from .base import BaseAppSettings
from pydantic import field_validator
import re

class DevelopmentSettings(BaseAppSettings):
    # Critical development overrides
    STRICT_VALIDATION: bool = False
    SECRET_KEY: str = "dev-secret-key-for-local-testing-only"
    
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