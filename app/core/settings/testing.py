# app/core/settings/testing.py
from .base import BaseAppSettings

class TestingSettings(BaseAppSettings):
    # Per i test potresti voler forzare l'uso di un database SQLite in memoria
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"
    # Eventuali altre override per semplificare i test possono essere aggiunte qui
