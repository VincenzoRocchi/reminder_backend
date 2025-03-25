# app/core/settings/testing.py
from .base import BaseAppSettings
from typing import Optional

class TestingSettings(BaseAppSettings):
    # Default to SQLite file database for testing
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    #overrides the default value of the TESTING environemnt variable