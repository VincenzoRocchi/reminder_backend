# app/core/settings/testing.py
from app.core.settings.base import BaseAppSettings
from pydantic import field_validator, Field
import os

class TestingSettings(BaseAppSettings):
    """Settings for the testing environment."""
    
    # Validate that we're using a test database configured in .env.testing
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if not v:
            raise ValueError(
                "SQLALCHEMY_DATABASE_URI must be set in testing environment. "
                "Please check your .env.testing file."
            )
        return v
    
    # Validate that we're using strict validation in testing
    @field_validator('STRICT_VALIDATION')
    def validate_strict_validation(cls, v):
        if v is False:
            raise ValueError(
                "STRICT_VALIDATION must be True in testing environment. "
                "If you need strict validation OFF, use the development environment instead "
                "by setting ENV=development."
            )
        return v