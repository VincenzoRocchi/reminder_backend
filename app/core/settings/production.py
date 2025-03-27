# app/core/settings/production.py
from .base import BaseAppSettings
from pydantic import field_validator
import logging

logger = logging.getLogger(__name__)

class ProductionSettings(BaseAppSettings):
    # Validate that we're using strict validation in production
    @field_validator('STRICT_VALIDATION')
    def validate_strict_validation(cls, v):
        if v is False:
            error_msg = "STRICT_VALIDATION must be True in production environment for security reasons"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        return v
    
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
    
    # Add extra validators for production (db engine)
    @field_validator('DB_ENGINE')
    def validate_db_engine(cls, v):
        if v == 'sqlite':
            raise ValueError(
                "Development must use a proper database engine, (mysql+pymysql, postgresql), not SQLite. "
                "SQLite is only for testing environment."
            )
        return v
    
    # Add extra validators for production (db uri)
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if not v:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.production file."
            )
        
        if "localhost" in v or "127.0.0.1" in v:
            error_msg = "Production database should not be on localhost"
            logger.warning(error_msg)
            # Warning only as this might be valid in some deployment scenarios
        
        if not "ssl=true" in v and "mysql" in v:
            error_msg = "Production MySQL connection should use SSL"
            logger.warning(error_msg)
        
        return v
    
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
    
    # Redis validation for production
    @field_validator('USE_REDIS')
    def validate_redis_usage(cls, v):
        if not v:
            error_msg = "Redis must be enabled in production for performance and security"
            logger.critical(error_msg)
            raise ValueError(error_msg)
        return v
    
    # Token expiration validation for production (stricter settings)
    @field_validator('ACCESS_TOKEN_EXPIRE_MINUTES')
    def validate_access_token_expiration(cls, v):
        if v < 15:  # Minimum 15 minutes for access tokens in production
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be at least 15 minutes in production")
        if v > 45:  # Maximum 45 minutes for access tokens in production
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 45 minutes in production")
        return v
    
    @field_validator('REFRESH_TOKEN_EXPIRE_DAYS')
    def validate_refresh_token_expiration(cls, v):
        if v < 7:  # Minimum 7 days for refresh tokens in production
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be at least 7 days in production")
        if v > 30:  # Maximum 30 days for refresh tokens in production
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS should not exceed 30 days in production")
        return v
    
    @field_validator('PASSWORD_RESET_TOKEN_EXPIRE_MINUTES')
    def validate_password_reset_expiration(cls, v):
        if v < 15:  # Minimum 15 minutes for password reset in production
            raise ValueError("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES must be at least 15 minutes in production")
        if v > 30:  # Maximum 30 minutes for password reset in production
            raise ValueError("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES should not exceed 30 minutes in production")
        return v