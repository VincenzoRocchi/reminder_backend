# app/core/settings/testing.py
from .base import BaseAppSettings

class TestingSettings(BaseAppSettings):
    # Default to SQLite file database for testing
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    
    # Testing-specific overrides
    STRICT_VALIDATION: bool = True