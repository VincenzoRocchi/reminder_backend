# app/core/settings/testing.py
from app.core.settings.base import BaseAppSettings
from pydantic import field_validator, Field
import os

class TestingSettings(BaseAppSettings):
    """Settings for the testing environment."""
    
    # ------------------------------
    # DATABASE SETTINGS
    # ------------------------------
    # Validate that we're using SQLite for testing
    @field_validator('DB_ENGINE')
    def validate_db_engine(cls, v):
        if v != 'sqlite':
            raise ValueError(
                "Testing environment should use SQLite for database engine."
            )
        return v
    
    # Validate database URI if explicitly provided
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if not v:
            raise ValueError(
                "No database connection configured. Please set DB_ENGINE and DB_NAME in your .env.testing file."
            )
        return v
    
    # ------------------------------
    # SECURITY SETTINGS
    # ------------------------------
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

    # Validate that we're using a test secret key
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v.startswith("test-") and not v.startswith("testing-"):
            raise ValueError(
                "Testing environment must use a test-specific secret key. "
                "Please set SECRET_KEY in your .env.testing file with a value starting with 'test-' or 'testing-'"
            )
        return v
    
    # Token expiration validation for testing (looser settings)
    @field_validator('ACCESS_TOKEN_EXPIRE_MINUTES')
    def validate_access_token_expiration(cls, v):
        if v < 5:  # Minimum 5 minutes for access tokens in testing
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 5 minutes in testing")
        if v > 120:  # Maximum 2 hours for access tokens in testing
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 120 minutes in testing")
        return v
    
    @field_validator('REFRESH_TOKEN_EXPIRE_DAYS')
    def validate_refresh_token_expiration(cls, v):
        if v < 1:  # Minimum 1 day for refresh tokens in testing
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be at least 1 day in testing")
        if v > 90:  # Maximum 90 days for refresh tokens in testing
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS should not exceed 90 days in testing")
        return v
    
    @field_validator('PASSWORD_RESET_TOKEN_EXPIRE_MINUTES')
    def validate_password_reset_expiration(cls, v):
        if v < 5:  # Minimum 5 minutes for password reset in testing
            raise ValueError("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES must be at least 5 minutes in testing")
        if v > 120:  # Maximum 2 hours for password reset in testing
            raise ValueError("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES should not exceed 120 minutes in testing")
        return v