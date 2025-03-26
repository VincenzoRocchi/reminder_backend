# app/core/settings/production.py
from .base import BaseAppSettings
from pydantic import field_validator
import logging

logger = logging.getLogger(__name__)

class ProductionSettings(BaseAppSettings):
    # add extra validators for production (cookies)
    @field_validator('SECURE_COOKIES')
    def validate_secure_cookies(cls, v):
        if not v:
            raise ValueError("SECURE_COOKIES must be True in production")
        return v
    
    # Secret key validation for production
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            error_msg = "Production SECRET_KEY must be at least 32 characters long"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        
        if v == "your-secret-key-here" or v == "test-secret-key-for-testing-only" or v == "development-secret-key-for-development-only":
            raise ValueError("Production SECRET_KEY must not use any default values")
        
        return v
    
    # Add extra validators for production (db host)
    @field_validator('DB_HOST')
    def validate_db_host(cls, v):
        if v == "localhost" or v == "127.0.0.1":
            raise ValueError("Production DB_HOST must not be localhost")
        return v
    
    # Add extra validators for production (db uri)
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if v and 'sqlite' in v.lower():
            raise ValueError("Production must use a proper database, not SQLite")
        return v
        
    # Use Redis for token storage - required in production
    USE_REDIS: bool = True
    
    # Twilio credentials validation
    @field_validator('TWILIO_ACCOUNT_SID')
    def validate_twilio_sid(cls, v):
        if not v or v.startswith("default") or len(v) < 10:
            error_msg = "Production TWILIO_ACCOUNT_SID must be set to a valid value"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        return v
        
    @field_validator('TWILIO_AUTH_TOKEN')  
    def validate_twilio_token(cls, v):
        if not v or v.startswith("default") or len(v) < 10:
            error_msg = "Production TWILIO_AUTH_TOKEN must be set to a valid value"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        return v
    
    # Email credentials validation
    @field_validator('SMTP_HOST')
    def validate_smtp_config(cls, v):
        if not v or v == "localhost":
            error_msg = "Production SMTP_HOST must be set to a valid host"
            logger.warning(error_msg)
            # Warning only, not raising error as email might be handled differently
        return v
    
    # Database validation
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_database_uri(cls, v):
        if not v:
            error_msg = "Production SQLALCHEMY_DATABASE_URI must be set"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        
        if "localhost" in v or "127.0.0.1" in v:
            error_msg = "Production database should not be on localhost"
            logger.warning(error_msg)
            # Warning only as this might be valid in some deployment scenarios
        
        if not "ssl=true" in v and "mysql" in v:
            error_msg = "Production MySQL connection should use SSL"
            logger.warning(error_msg)
        
        return v
        
    # Redis validation for production
    @field_validator('USE_REDIS')
    def validate_redis_usage(cls, v):
        if not v:
            error_msg = "Redis should be enabled in production for performance and security"
            logger.warning(error_msg)
        return v
    
    def model_post_init_handler(self, **kwargs):
        # No need to call super() if BaseAppSettings doesn't implement this method
        
        # Final validation of production settings
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.production file."
            )