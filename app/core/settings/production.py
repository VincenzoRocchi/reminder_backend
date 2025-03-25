# app/core/settings/production.py
from .base import BaseAppSettings
from pydantic import field_validator

class ProductionSettings(BaseAppSettings):
    # These must be provided in production and not use defaults
    SECRET_KEY: str 
    DB_HOST: str
    
    # Force these values in production regardless of .env
    STRICT_VALIDATION: bool = True
    SECURE_COOKIES: bool = True
    
    # Add extra validators for production
    @field_validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Production SECRET_KEY must be at least 32 characters")
        if v == "your-secret-key-here" or v == "dev-secret-key-for-local-testing-only":
            raise ValueError("Production SECRET_KEY must not use development defaults")
        return v
        
    @field_validator('DB_HOST')
    def validate_db_host(cls, v):
        if v == "localhost" or v == "127.0.0.1":
            raise ValueError("Production DB_HOST must not be localhost")
        return v
        
    @field_validator('SQLALCHEMY_DATABASE_URI')
    def validate_db_uri(cls, v):
        if v and ('sqlite' in v.lower()):
            raise ValueError("Production must use a proper database, not SQLite")
        return v
        
    def model_post_init(self, **kwargs):
        super().model_post_init(**kwargs)
        
        # Final validation of production settings
        if not self.SQLALCHEMY_DATABASE_URI:
            raise ValueError(
                "No database connection configured. Please set DB_HOST, DB_USER, "
                "DB_PASSWORD, and DB_NAME in your .env.production file."
            )