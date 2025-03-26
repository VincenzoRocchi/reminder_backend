# app/core/settings/base.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, SecretStr, field_validator, model_validator, ConfigDict
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Determina l'ambiente e carica il file .env appropriato
ENV = os.getenv("ENV", "development")
env_file = f".env.{ENV}"
if Path(env_file).exists():
    load_dotenv(env_file)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

class BaseAppSettings(BaseSettings):
    # ------------------------------
    # IMPOSTAZIONI API
    # ------------------------------
    API_V1_STR: str = Field(default="/api/v1", description="Prefisso per le API v1")
    PROJECT_NAME: str = Field(default="Reminder App API", description="Nome del progetto")
    
    # ------------------------------
    # IMPOSTAZIONI DATABASE (per MySQL)
    # ------------------------------
    DB_HOST: str = Field(default=os.getenv("DB_HOST", "localhost"), description="Host del database")
    DB_PORT: int = Field(default=int(os.getenv("DB_PORT", "3306")), description="Porta MySQL standard")
    DB_USER: str = Field(default=os.getenv("DB_USER", "root"), description="Utente del database")
    DB_PASSWORD: str = Field(default=os.getenv("DB_PASSWORD", "password"), description="Password del database")
    DB_NAME: str = Field(default=os.getenv("DB_NAME", "reminder_app"), description="Nome del database")
    DB_POOL_SIZE: int = Field(default=int(os.getenv("DB_POOL_SIZE", "5")), description="Dimensione iniziale del pool")
    DB_MAX_OVERFLOW: int = Field(default=int(os.getenv("DB_MAX_OVERFLOW", "10")), description="Connessioni aggiuntive quando il pool è pieno")
    DB_POOL_TIMEOUT: int = Field(default=int(os.getenv("DB_POOL_TIMEOUT", "30")), description="Timeout in secondi per ottenere una connessione")
    SQLALCHEMY_DATABASE_URI: Optional[str] = Field(
        default=None,
        description=("Stringa di connessione per SQLAlchemy. Se non impostata, "
                     "viene costruita usando DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME.")
    )
    
    # ------------------------------
    # IMPOSTAZIONI SICUREZZA
    # ------------------------------
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "your-secret-key-here"), description="Chiave segreta per la firma dei token JWT")
    ALGORITHM: str = Field(default=os.getenv("ALGORITHM", "HS256"), description="Algoritmo usato per la firma dei token JWT")
    JWT_TOKEN_PREFIX: str = Field(default=os.getenv("JWT_TOKEN_PREFIX", "Bearer"), description="Prefisso per l'header Authorization")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")), description="Durata del token di accesso (in minuti)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")), description="Durata del token di refresh (in giorni)")
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "15")), description="Durata del token di reset password (in minuti)")
    
    # ------------------------------
    # IMPOSTAZIONI EMAIL
    # ------------------------------
    SMTP_HOST: str = Field(default=os.getenv("SMTP_HOST", ""), description="Host del server SMTP")
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="Porta SMTP (587 per TLS)")
    SMTP_USER: str = Field(default=os.getenv("SMTP_USER", ""), description="Username SMTP")
    SMTP_PASSWORD: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="Password SMTP")
    EMAIL_FROM: str = Field(default=os.getenv("EMAIL_FROM", "noreply@reminderapp.com"), description="Indirizzo mittente")
    
    # ------------------------------
    # IMPOSTAZIONI SMS (TWILIO)
    # ------------------------------
    TWILIO_ACCOUNT_SID: str = Field(default=os.getenv("TWILIO_ACCOUNT_SID", ""), description="SID account Twilio")
    TWILIO_AUTH_TOKEN: str = Field(default=os.getenv("TWILIO_AUTH_TOKEN", ""), description="Token di autenticazione Twilio")
    TWILIO_PHONE_NUMBER: str = Field(default=os.getenv("TWILIO_PHONE_NUMBER", ""), description="Numero di telefono Twilio")
    
    # ------------------------------
    # IMPOSTAZIONI WHATSAPP
    # ------------------------------
    WHATSAPP_API_KEY: str = Field(default=os.getenv("WHATSAPP_API_KEY", ""), description="Chiave API WhatsApp")
    WHATSAPP_API_URL: str = Field(default=os.getenv("WHATSAPP_API_URL", ""), description="URL endpoint API WhatsApp")
    
    # ------------------------------
    # IMPOSTAZIONI STRIPE (GATEWAY PAGAMENTI)
    # ------------------------------
    STRIPE_API_KEY: str = Field(default=os.getenv("STRIPE_API_KEY", ""), description="Chiave API Stripe")
    STRIPE_WEBHOOK_SECRET: str = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET", ""), description="Segreto webhook Stripe")
    PAYMENT_SUCCESS_URL: str = Field(default=os.getenv("PAYMENT_SUCCESS_URL", "http://localhost:3000/payment/success"), description="URL di reindirizzamento dopo un pagamento riuscito")
    PAYMENT_CANCEL_URL: str = Field(default=os.getenv("PAYMENT_CANCEL_URL", "http://localhost:3000/payment/cancel"), description="URL di reindirizzamento dopo un pagamento annullato")
    
    # ------------------------------
    # IMPOSTAZIONI AMBIENTE
    # ------------------------------
    ENV: str = Field(default=ENV, description="Ambiente corrente (development, testing, production)")
    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENV == "development"
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENV == "production"
    @property
    def IS_TESTING(self) -> bool:
        return self.ENV == "testing"
    
    STRICT_VALIDATION: bool = Field(
        default=os.getenv("STRICT_VALIDATION", "True" if ENV != "development" else "False").lower() == "true",
        description="Enforce strict validation of sensitive data"
    )
    def should_validate(self, validation_type: str = "all") -> bool:
        if self.IS_PRODUCTION:
            return True
        return self.STRICT_VALIDATION
    # ------------------------------
    # IMPOSTAZIONI LOGGING
    # ------------------------------
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), description="Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    LOG_FORMAT: str = Field(default=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"), description="Formato dei messaggi di log")
    
    # ------------------------------
    # IMPOSTAZIONI CORS
    # ------------------------------
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")],
        description="Origini permesse per le richieste CORS (separate da virgola)"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true", description="Abilita l'invio di credenziali nelle richieste CORS")
    
    # ------------------------------
    # IMPOSTAZIONI SCHEDULER
    # ------------------------------
    SCHEDULER_TIMEZONE: str = Field(default=os.getenv("SCHEDULER_TIMEZONE", "UTC"), description="Fuso orario per lo scheduler (default: UTC)")
    
    # ------------------------------
    # SICUREZZA COOKIE
    # ------------------------------
    # Replace the property with a field definition
    SECURE_COOKIES: bool = Field(
        default_factory=lambda: os.getenv("SECURE_COOKIES", "False" if ENV == "development" else "True").lower() == "true",
        description="Abilita flag 'secure' sui cookie (True in produzione, False in sviluppo)"
    )
    
    # ------------------------------
    # CONFIGURAZIONE STORAGE AWS S3
    # ------------------------------
    STORAGE_TYPE: str = Field(default=os.getenv("STORAGE_TYPE", "local"), pattern=r"^(s3|local)$", description="Tipo di storage: 's3' per AWS S3, 'local' per filesystem locale")
    S3_BUCKET_NAME: Optional[str] = Field(default=os.getenv("S3_BUCKET_NAME"), min_length=3, pattern=r"^[a-z0-9.-]{3,63}$", examples=["my-production-bucket"], description="Nome del bucket S3 (se STORAGE_TYPE='s3')")
    S3_ACCESS_KEY: Optional[SecretStr] = Field(default=(SecretStr(os.getenv("S3_ACCESS_KEY", "")) if os.getenv("S3_ACCESS_KEY") else None), min_length=20, description="Chiave di accesso per AWS S3 (se STORAGE_TYPE='s3')")
    S3_SECRET_KEY: Optional[SecretStr] = Field(default=(SecretStr(os.getenv("S3_SECRET_KEY", "")) if os.getenv("S3_SECRET_KEY") else None), min_length=40, description="Chiave segreta per AWS S3 (se STORAGE_TYPE='s3')")
    S3_REGION: Optional[str] = Field(default=os.getenv("S3_REGION"), pattern=r"^[a-z]{2}-[a-z]+-\d$", examples=["us-east-1"], description="Regione AWS per il bucket S3 (se STORAGE_TYPE='s3')")
    S3_OBJECT_ACL: str = Field(default=os.getenv("S3_OBJECT_ACL", "private"), pattern=r"^(private|public-read)$", description="ACL per gli oggetti S3")
    
    # ------------------------------
    # RATE LIMITING
    # ------------------------------
    RATE_LIMIT_ENABLED: bool = Field(default=os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true", description="Abilita/disabilita il rate limiting sulle API")
    DEFAULT_RATE_LIMIT: str = Field(default=os.getenv("DEFAULT_RATE_LIMIT", "100/minute"), description='Limite di default (es: "100/minute")')
    
    # ------------------------------
    # DOCUMENTAZIONE API
    # ------------------------------
    DOCS_URL: str = Field(default=os.getenv("DOCS_URL", "/docs"), description="URL per la documentazione Swagger UI")
    REDOC_URL: str = Field(default=os.getenv("REDOC_URL", "/redoc"), description="URL per la documentazione ReDoc")
    OPENAPI_URL: str = Field(default=os.getenv("OPENAPI_URL", "/openapi.json"), description="URL per il file OpenAPI JSON")
    
    # ------------------------------
    # CONFIGURAZIONE REDIS
    # ------------------------------
    REDIS_URL: str = Field(
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="URL di connessione Redis (es: redis://localhost:6379/0)"
    )
    REDIS_PASSWORD: Optional[SecretStr] = Field(
        default=SecretStr(os.getenv("REDIS_PASSWORD", "")) if os.getenv("REDIS_PASSWORD") else None,
        description="Password Redis (opzionale)"
    )
    REDIS_SSL_ENABLED: bool = Field(
        default=os.getenv("REDIS_SSL_ENABLED", "False").lower() == "true",
        description="Abilita connessione SSL per Redis"
    )
    REDIS_CONNECTION_TIMEOUT: int = Field(
        default=int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5")),
        description="Timeout in secondi per la connessione Redis"
    )
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(
        default=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
        description="Intervallo in secondi per il controllo dello stato Redis"
    )
    
    # ------------------------------
    # CONFIGURAZIONE PYDANTIC
    # ------------------------------
    model_config = ConfigDict(
        env_file=env_file if Path(env_file).exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # ------------------------------
    # LOAD SECRETS METHOD
    # ------------------------------
    def load_secrets(self) -> None:
        """Load sensitive configuration from encrypted secrets"""
        try:
            # Import here to avoid circular imports
            from app.core.secrets_manager import secrets_manager, SecretsError
            
            # Database credentials
            db_secrets = secrets_manager.get_category('database')
            if db_secrets:
                if 'password' in db_secrets:
                    self.DB_PASSWORD = db_secrets['password']
                if 'user' in db_secrets:
                    self.DB_USER = db_secrets['user']
                if 'host' in db_secrets:
                    self.DB_HOST = db_secrets['host']
                if 'port' in db_secrets:
                    self.DB_PORT = int(db_secrets['port'])
                if 'name' in db_secrets:
                    self.DB_NAME = db_secrets['name']
            
            # Security credentials
            security_secrets = secrets_manager.get_category('security')
            if security_secrets:
                if 'secret_key' in security_secrets:
                    self.SECRET_KEY = security_secrets['secret_key']
            
            # Email service credentials
            email_secrets = secrets_manager.get_category('email')
            if email_secrets:
                if 'smtp_password' in email_secrets:
                    self.SMTP_PASSWORD = email_secrets['smtp_password']
                if 'smtp_user' in email_secrets:
                    self.SMTP_USER = email_secrets['smtp_user']
                if 'smtp_host' in email_secrets:
                    self.SMTP_HOST = email_secrets['smtp_host']
            
            # SMS service credentials
            sms_secrets = secrets_manager.get_category('sms')
            if sms_secrets:
                if 'twilio_auth_token' in sms_secrets:
                    self.TWILIO_AUTH_TOKEN = sms_secrets['twilio_auth_token']
                if 'twilio_account_sid' in sms_secrets:
                    self.TWILIO_ACCOUNT_SID = sms_secrets['twilio_account_sid']
            
            # WhatsApp service credentials
            whatsapp_secrets = secrets_manager.get_category('whatsapp')
            if whatsapp_secrets:
                if 'api_key' in whatsapp_secrets:
                    self.WHATSAPP_API_KEY = whatsapp_secrets['api_key']
                if 'api_url' in whatsapp_secrets:
                    self.WHATSAPP_API_URL = whatsapp_secrets['api_url']
            
            # Payment service credentials
            payment_secrets = secrets_manager.get_category('payment')
            if payment_secrets:
                if 'stripe_api_key' in payment_secrets:
                    self.STRIPE_API_KEY = payment_secrets['stripe_api_key']
                if 'stripe_webhook_secret' in payment_secrets:
                    self.STRIPE_WEBHOOK_SECRET = payment_secrets['stripe_webhook_secret']
            
            # S3 credentials
            s3_secrets = secrets_manager.get_category('s3')
            if s3_secrets:
                if 'access_key' in s3_secrets and s3_secrets['access_key']:
                    self.S3_ACCESS_KEY = s3_secrets['access_key']
                if 'secret_key' in s3_secrets and s3_secrets['secret_key']:
                    self.S3_SECRET_KEY = s3_secrets['secret_key']
            
            # Redis credentials
            redis_secrets = secrets_manager.get_category('redis')
            if redis_secrets:
                if 'password' in redis_secrets:
                    self.REDIS_PASSWORD = redis_secrets['password']
                if 'url' in redis_secrets:
                    self.REDIS_URL = redis_secrets['url']
                    
        except Exception as e:
            # Log the error but continue with environment variables
            logger.warning(f"Failed to load secrets: {str(e)}")
            logger.warning("Falling back to environment variables")
    
    # ------------------------------
    # VALIDATORI
    # ------------------------------
    @field_validator("STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        if v not in {"s3", "local"}:
            raise ValueError("Storage type must be 's3' or 'local'")
        return v

    @model_validator(mode="before")
    def build_sqlalchemy_uri(cls, values: dict) -> dict:
        # If URI is already specified in the environment, use that
        if values.get("SQLALCHEMY_DATABASE_URI"):
            return values
            
        # Only build a URI if we have all the required components
        db_host = values.get('DB_HOST')
        db_user = values.get('DB_USER')
        db_password = values.get('DB_PASSWORD')
        db_name = values.get('DB_NAME')
        db_port = values.get('DB_PORT')
        
        if all([db_host, db_user, db_password, db_name, db_port]):
            # Build the URI - we'll let the environment-specific settings
            # decide whether to use it or enforce their own rules
            uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Add SSL for non-development environments
            env = values.get('ENV', '').lower()
            if env != "development":
                uri += "?ssl=true"
                
            values["SQLALCHEMY_DATABASE_URI"] = uri
            
        return values

    @model_validator(mode="after")
    def validate_s3_config(self) -> "BaseAppSettings":
        if self.STORAGE_TYPE == "s3":
            missing = []
            if not self.S3_BUCKET_NAME:
                missing.append("S3_BUCKET_NAME")
            if not self.S3_ACCESS_KEY:
                missing.append("S3_ACCESS_KEY")
            if not self.S3_SECRET_KEY:
                missing.append("S3_SECRET_KEY")
            if not self.S3_REGION:
                missing.append("S3_REGION")
            if missing:
                raise ValueError(f"Missing required S3 configuration for storage type 's3': {', '.join(missing)}")
            if self.S3_BUCKET_NAME and (".." in self.S3_BUCKET_NAME or self.S3_BUCKET_NAME.startswith("-")):
                raise ValueError("Invalid S3 bucket name format")
        return self
        
    @model_validator(mode='after')
    def load_encrypted_secrets(self) -> 'BaseAppSettings':
        self.load_secrets()
        return self

    @property
    def s3_credentials_provided(self) -> bool:
        return all([self.S3_ACCESS_KEY, self.S3_SECRET_KEY, self.S3_REGION, self.S3_BUCKET_NAME])
    
    def validate_settings(self) -> None:
        if self.IS_PRODUCTION:
            assert self.SECRET_KEY != "your-secret-key-here", "Production SECRET_KEY must be set"
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY should be at least 32 characters in production"
            assert self.DB_HOST != "localhost", "Production DB_HOST should not be localhost"
            if any([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]):
                assert all([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]), "SMTP settings incomplete"