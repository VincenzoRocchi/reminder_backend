# app/core/settings/base.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, SecretStr, field_validator, model_validator, ConfigDict
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Get the environment and load the appropriate .env file
ENV = os.getenv("ENV", "development")
env_file = f".env.{ENV}"
if Path(env_file).exists():
    load_dotenv(env_file)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

class BaseAppSettings(BaseSettings):
    # ------------------------------
    # API SETTINGS
    # ------------------------------
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    PROJECT_NAME: str = Field(default="Reminder App API", description="Project name")
    
    # ------------------------------
    # DATABASE SETTINGS
    # ------------------------------
    DB_HOST: str = Field(default=os.getenv("DB_HOST", "localhost"), description="Database host")
    DB_PORT: int = Field(default=int(os.getenv("DB_PORT", "3306")), description="Standard MySQL port")
    DB_USER: str = Field(default=os.getenv("DB_USER", "root"), description="Database user")
    DB_PASSWORD: str = Field(default=os.getenv("DB_PASSWORD", "password"), description="Database password")
    DB_NAME: str = Field(default=os.getenv("DB_NAME", "reminder_app"), description="Database name")
    DB_POOL_SIZE: int = Field(default=int(os.getenv("DB_POOL_SIZE", "5")), description="Initial pool size")
    DB_MAX_OVERFLOW: int = Field(default=int(os.getenv("DB_MAX_OVERFLOW", "10")), description="Additional connections when pool is full")
    DB_POOL_TIMEOUT: int = Field(default=int(os.getenv("DB_POOL_TIMEOUT", "30")), description="Timeout in seconds to get a connection")
    SQL_ECHO: bool = Field(default=os.getenv("SQL_ECHO", "False").lower() == "true", description="Enable SQL query logging")
    SQLALCHEMY_DATABASE_URI: Optional[str] = Field(
        default=os.getenv("SQLALCHEMY_DATABASE_URI"),
        description=("SQLAlchemy connection string. If not set, "
                     "it will be built using DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME.")
    )
    
    @model_validator(mode='after')
    def build_sqlalchemy_uri(self) -> 'BaseAppSettings':
        # If URI is already specified in the environment, use that
        if self.SQLALCHEMY_DATABASE_URI:
            return self
        
        # Only build a URI if we have all the required components
        if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, self.DB_PORT]):
            # Build the URI - we'll let the environment-specific settings
            # decide whether to use it or enforce their own rules
            uri = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            
            # Add SSL for non-development environments
            if self.ENV != "development":
                uri += "?ssl=true"
            
            self.SQLALCHEMY_DATABASE_URI = uri
        
        return self
    
    # ------------------------------
    # SECURITY SETTINGS
    # ------------------------------
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "your-secret-key-here"), description="Secret key for JWT token signing")
    ALGORITHM: str = Field(default=os.getenv("ALGORITHM", "HS256"), description="Algorithm used for JWT token signing")
    JWT_TOKEN_PREFIX: str = Field(default=os.getenv("JWT_TOKEN_PREFIX", "Bearer"), description="Prefix for Authorization header")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")), description="Access token expiration (in minutes)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")), description="Refresh token expiration (in days)")
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "15")), description="Password reset token expiration (in minutes)")
    
    # ------------------------------
    # EMAIL SETTINGS
    # ------------------------------
    SMTP_HOST: str = Field(default=os.getenv("SMTP_HOST", ""), description="SMTP server host")
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="SMTP port (587 for TLS)")
    SMTP_USER: str = Field(default=os.getenv("SMTP_USER", ""), description="SMTP username")
    SMTP_PASSWORD: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="SMTP password")
    EMAIL_FROM: str = Field(default=os.getenv("EMAIL_FROM", "noreply@reminderapp.com"), description="From email address")
    
    # ------------------------------
    # SMS SETTINGS (TWILIO)
    # ------------------------------
    TWILIO_ACCOUNT_SID: str = Field(default=os.getenv("TWILIO_ACCOUNT_SID", ""), description="Twilio account SID")
    TWILIO_AUTH_TOKEN: str = Field(default=os.getenv("TWILIO_AUTH_TOKEN", ""), description="Twilio authentication token")
    TWILIO_PHONE_NUMBER: str = Field(default=os.getenv("TWILIO_PHONE_NUMBER", ""), description="Twilio phone number")
    
    # ------------------------------
    # WHATSAPP SETTINGS
    # ------------------------------
    WHATSAPP_API_KEY: str = Field(default=os.getenv("WHATSAPP_API_KEY", ""), description="WhatsApp API key")
    WHATSAPP_API_URL: str = Field(default=os.getenv("WHATSAPP_API_URL", ""), description="WhatsApp API endpoint URL")
    
    # ------------------------------
    # STRIPE SETTINGS (PAYMENT GATEWAY)
    # ------------------------------
    STRIPE_API_KEY: str = Field(default=os.getenv("STRIPE_API_KEY", ""), description="Stripe API key")
    STRIPE_WEBHOOK_SECRET: str = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET", ""), description="Stripe webhook secret")
    PAYMENT_SUCCESS_URL: str = Field(default=os.getenv("PAYMENT_SUCCESS_URL", "http://localhost:3000/payment/success"), description="Redirect URL after successful payment")
    PAYMENT_CANCEL_URL: str = Field(default=os.getenv("PAYMENT_CANCEL_URL", "http://localhost:3000/payment/cancel"), description="Redirect URL after canceled payment")
    
    # ------------------------------
    # ENVIRONMENT SETTINGS
    # ------------------------------
    ENV: str = Field(default=ENV, description="Current environment (development, testing, production)")
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
    
    # ------------------------------
    # LOGGING SETTINGS
    # ------------------------------
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    LOG_FORMAT: str = Field(default=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"), description="Log message format")
    
    # ------------------------------
    # CORS SETTINGS
    # ------------------------------
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:4200"],
        description="Allowed origins for CORS requests (JSON array or comma-separated string)"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true", description="Enable sending credentials in CORS requests")
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from environment which could be a JSON array or a comma-separated string"""
        import json
        from typing import List
        import logging
        
        logger = logging.getLogger(__name__)
        
        if isinstance(v, List):
            return v
        
        if isinstance(v, str):
            # Try parsing as JSON first
            try:
                origins = json.loads(v)
                if isinstance(origins, List):
                    return origins
            except json.JSONDecodeError:
                # If JSON parsing fails, try comma-separated format
                pass
            
            # Fall back to comma-separated format
            if ',' in v:
                return [origin.strip() for origin in v.split(',') if origin.strip()]
            elif v.strip():
                # Single value
                return [v.strip()]
        
        # Default if all parsing fails
        logger.warning(f"Could not parse CORS_ORIGINS: {v}, using default")
        return ["http://localhost:4200"]
    
    # ------------------------------
    # SCHEDULER SETTINGS
    # ------------------------------
    SCHEDULER_TIMEZONE: str = Field(default=os.getenv("SCHEDULER_TIMEZONE", "UTC"), description="Timezone for scheduler (default: UTC)")
    
    # ------------------------------
    # COOKIE SECURITY
    # ------------------------------
    SECURE_COOKIES: bool = Field(
        default_factory=lambda: os.getenv("SECURE_COOKIES", "False" if ENV == "development" else "True").lower() == "true",
        description="Enable 'secure' flag on cookies (True in production, False in development)"
    )
    
    # ------------------------------
    # RATE LIMITING
    # ------------------------------
    RATE_LIMIT_ENABLED: bool = Field(default=os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true", description="Enable/disable API rate limiting")
    DEFAULT_RATE_LIMIT: str = Field(default=os.getenv("DEFAULT_RATE_LIMIT", "100/minute"), description='Default limit (e.g. "100/minute")')
    
    # ------------------------------
    # API DOCUMENTATION
    # ------------------------------
    DOCS_URL: str = Field(default=os.getenv("DOCS_URL", "/docs"), description="URL for Swagger UI documentation")
    REDOC_URL: str = Field(default=os.getenv("REDOC_URL", "/redoc"), description="URL for ReDoc documentation")
    OPENAPI_URL: str = Field(default=os.getenv("OPENAPI_URL", "/openapi.json"), description="URL for OpenAPI JSON file")
    
    # ------------------------------
    # REDIS CONFIGURATION
    # ------------------------------
    REDIS_URL: str = Field(
        default=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="Redis connection URL (e.g. redis://localhost:6379/0)"
    )
    REDIS_PASSWORD: Optional[SecretStr] = Field(
        default=SecretStr(os.getenv("REDIS_PASSWORD", "")) if os.getenv("REDIS_PASSWORD") else None,
        description="Redis password (optional)"
    )
    REDIS_SSL_ENABLED: bool = Field(
        default=os.getenv("REDIS_SSL_ENABLED", "False").lower() == "true",
        description="Enable SSL connection for Redis"
    )
    REDIS_CONNECTION_TIMEOUT: int = Field(
        default=int(os.getenv("REDIS_CONNECTION_TIMEOUT", "5")),
        description="Timeout in seconds for Redis connection"
    )
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(
        default=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
        description="Interval in seconds for Redis health check"
    )
    USE_REDIS: bool = Field(
        default=os.getenv("USE_REDIS", "True").lower() == "true",
        description="Whether to use Redis for tokens and caching (required in production, optional in development/testing)"
    )
    
    # ------------------------------
    # PYDANTIC CONFIGURATION
    # ------------------------------
    model_config = ConfigDict(
        env_file=env_file if Path(env_file).exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )