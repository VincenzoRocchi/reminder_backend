# app/core/settings/production.py
from .base import BaseAppSettings

class ProductionSettings(BaseAppSettings):
    # In produzione, il SECRET_KEY deve essere fornito tramite variabile d'ambiente
    SECRET_KEY: str
    # Forza DB_HOST a non essere localhost
    DB_HOST: str
    # Altre impostazioni che devono essere forzate in produzione possono essere aggiunte qui.
