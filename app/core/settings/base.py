# app/core/settings/base.py
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, SecretStr, field_validator, model_validator, ConfigDict
import os
import logging
from pathlib import Path

# Get the environment - no need to load dotenv here, it's already loaded in __init__.py
ENV = os.getenv("ENV", "development").lower()

logger = logging.getLogger(__name__)

class BaseAppSettings(BaseSettings):
    # ------------------------------
    # SERVER SETTINGS
    # ------------------------------
    SERVER_HOST: str = Field(
        default=os.getenv("SERVER_HOST", "127.0.0.1" if ENV == "testing" else "0.0.0.0"),
        description="Host interface to bind the server to"
    )
    SERVER_PORT: int = Field(
        default=int(os.getenv("SERVER_PORT", "8000" if ENV == "testing" else "5000")),
        description="Port to run the server on"
    )
    SERVER_RELOAD: bool = Field(
        default=os.getenv("SERVER_RELOAD", "True" if ENV == "testing" or ENV == "development" else "False").lower() == "true",
        description="Enable auto-reload for development"
    )
    SERVER_WORKERS: int = Field(
        default=int(os.getenv("SERVER_WORKERS", "1" if ENV == "testing" else "4")),
        description="Number of worker processes"
    )
    SERVER_LOG_LEVEL: str = Field(
        default=os.getenv("SERVER_LOG_LEVEL", "debug" if ENV == "testing" else "info"),
        description="Server log level"
    )
    
    # ------------------------------
    # API SETTINGS
    # ------------------------------
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    PROJECT_NAME: str = Field(default="Reminder App API", description="Project name")
    
    # ------------------------------
    # DATABASE SETTINGS
    # ------------------------------
    DB_ENGINE: str = Field(default=os.getenv("DB_ENGINE", "mysql+pymysql"), description="Database engine (e.g. mysql+pymysql, postgresql, sqlite)")
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
        
        # Special case for SQLite
        if self.DB_ENGINE == 'sqlite':
            self.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.DB_NAME}"
            return self
        
        # Only build a URI if we have all the required components for other database types
        if all([self.DB_HOST, self.DB_USER, self.DB_PASSWORD, self.DB_NAME, self.DB_PORT]):
            # Build the URI using the configured engine
            uri = f"{self.DB_ENGINE}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            
            # Add SSL for non-development environments
            if self.ENV != "development":
                uri += "?ssl=true"
            
            self.SQLALCHEMY_DATABASE_URI = uri
        
        return self
    
    # ------------------------------
    # SECURITY SETTINGS
    # ------------------------------
    SECRET_KEY: str = Field(
        default=os.getenv("SECRET_KEY", "your-secret-key-here"), 
        description="Secret key for JWT token signing. Must be at least 32 characters in production."
    )
    ALGORITHM: str = Field(
        default=os.getenv("ALGORITHM", "HS256"), 
        description="Algorithm used for JWT token signing"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")), 
        description="Access token expiration (in minutes). Default: 60 minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")), 
        description="Refresh token expiration (in days). Default: 30 days"
    )
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = Field(
        default=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "30")), 
        description="Password reset token expiration (in minutes). Default: 30 minutes"
    )
    
    # ------------------------------
    # TWILIO SETTINGS (SMS & WHATSAPP)
    # ------------------------------
    TWILIO_ACCOUNT_SID: str = Field(default=os.getenv("TWILIO_ACCOUNT_SID", ""), description="Twilio account SID")
    TWILIO_AUTH_TOKEN: str = Field(default=os.getenv("TWILIO_AUTH_TOKEN", ""), description="Twilio authentication token")
    # Each client will provide their own phone number when sending messages
    # No default phone number is stored in application settings
    
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
    
    # Add the missing should_validate method
    def should_validate(self, validation_type: str = 'all') -> bool:
        """
        Determines if validation should be enforced based on settings.
        
        Args:
            validation_type: Type of validation to check ('all', 'format', 'security', etc.)
            
        Returns:
            bool: True if validation should be enforced, False otherwise
        """
        # If strict validation is enabled, always validate
        if self.STRICT_VALIDATION:
            return True
            
        # For critical security validations, always validate regardless of STRICT_VALIDATION
        if validation_type == 'security':
            return True
            
        # In development, be more lenient with some validation types
        if self.IS_DEVELOPMENT:
            # We might want to allow some validation types to be bypassed in development
            if validation_type in ['format', 'length']:
                return False
        
        # In production, always validate unless explicitly disabled
        if self.IS_PRODUCTION:
            return True
            
        # Default behavior for other environments/validation types
        return False
    
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
    
    DISABLE_SCHEDULER: bool = Field(
        default=os.getenv("DISABLE_SCHEDULER", "False").lower() == "true", 
        description="Disable the reminder scheduler service completely"
    )
    
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
    
    @field_validator('USE_REDIS')
    def validate_redis_usage(cls, v):
        if v:
            logger.info("Redis is enabled")
        else:
            logger.info("Using in-memory storage")
        return v
    
    # ------------------------------
    # PYDANTIC CONFIGURATION
    # ------------------------------
    # Only look in env directory
    @staticmethod
    def _find_env_file():
        env = os.getenv("ENV", "development")
        paths = [
            Path(f"env/.env.{env}"),
            Path("env/.env")
        ]
        
        for path in paths:
            if path.exists():
                return str(path)
        
        return None
    
    model_config = ConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )