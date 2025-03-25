# app/core/settings/production.py
from .base import BaseAppSettings
from pydantic import field_validator

class ProductionSettings(BaseAppSettings):
    # add extra validators for production (cookies)
    @field_validator('SECURE_COOKIES')
    def validate_secure_cookies(cls, v):
        if not v:
            raise ValueError("SECURE_COOKIES must be True in production")
        return v
    
    # Add extra validators for production (secret key)
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Production SECRET_KEY must be at least 32 characters")
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
        
    def model_post_init_handler(self, **kwargs):
        # No need to call super() if BaseAppSettings doesn't implement this method
        
        # Final validation of production settings
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.production file."
            )