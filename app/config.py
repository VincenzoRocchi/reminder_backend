from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost/dbname"
    secret_key: str = "your_secret_key"
    debug: bool = False

    class Config:
        env_file = ".env"  # Indica il file da cui leggere le variabili

# Crea un'istanza globale da importare ovunque
settings = Settings()