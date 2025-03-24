# app/core/settings/development.py
from .base import BaseAppSettings

class DevelopmentSettings(BaseAppSettings):
    # In ambiente di sviluppo potresti voler usare un SECRET_KEY meno critico
    # oppure lasciare le impostazioni di default.
    SECRET_KEY: str = "your-secret-key-here"  # Valore di default per sviluppo
    # Puoi aggiungere altre override se necessario
