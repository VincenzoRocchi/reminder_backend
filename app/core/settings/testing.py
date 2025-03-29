# app/core/settings/testing.py
from app.core.settings.base import BaseAppSettings
from pydantic import field_validator, Field, model_validator
import os
import logging
from app.core.exceptions import InvalidConfigurationError, SecurityException

logger = logging.getLogger(__name__)

class TestingSettings(BaseAppSettings):
    """Settings for the testing environment."""
    
    # =======================================================================
    # DATABASE VALIDATORS
    # =======================================================================
    
    # Validate that we're using SQLite for testing
    @field_validator('DB_ENGINE')
    def validate_db_engine(cls, v):
        if v != 'sqlite':
            raise InvalidConfigurationError(
                code="INVALID_DB_ENGINE",
                message="Testing environment should use SQLite for database engine."
            )
        return v
    
    # Validate database configuration after all values are set
    @model_validator(mode='after')
    def validate_db_config(self) -> 'TestingSettings':
        if not self.SQLALCHEMY_DATABASE_URI:
            # Check for SQLite configuration first
            if self.DB_ENGINE == 'sqlite':
                # Build appropriate SQLite URI based on DB_NAME
                if self.DB_NAME == ":memory:":
                    self.SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
                else:
                    self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.DB_NAME}"
                logger.debug(f"Using SQLite database: {self.SQLALCHEMY_DATABASE_URI}")
                return self
            
            # If we get here, we don't have a valid configuration
            raise InvalidConfigurationError(
                code="MISSING_DB_CONFIG",
                message="No database connection configured. Please set DB_ENGINE and DB_NAME in your .env.testing file."
            )
        return self
    
    # =======================================================================
    # SECURITY VALIDATORS
    # =======================================================================
    
    # Validate that we're using strict validation in testing
    @field_validator('STRICT_VALIDATION')
    def validate_strict_validation(cls, v):
        if v is False:
            logger.error(
                "STRICT_VALIDATION must be True in testing environment. "
                "Setting it to False would invalidate test results as validation errors would be ignored."
            )
            raise SecurityException(
                code="INVALID_SECURITY_CONFIG",
                message="STRICT_VALIDATION must be True in testing environment. "
                "Setting it to False would invalidate test results as validation errors would be ignored."
            )
        return v

    # Validate that we're using a test secret key
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if not v.startswith("test-") and not v.startswith("testing-"):
            raise SecurityException(
                code="INVALID_TEST_SECRET_KEY",
                message="Testing environment must use a test-specific secret key. "
                "Please set SECRET_KEY in your .env.testing file with a value starting with 'test-' or 'testing-'"
            )
        return v