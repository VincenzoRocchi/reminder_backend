from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field, SecretStr, field_validator, model_validator, ConfigDict
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Reminder App API"
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "reminder_app")
    
    # Database Pool
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        uri = f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        if not self.IS_DEVELOPMENT:
            # Add SSL for production/staging
            uri += "?ssl=true"
        return uri
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Email
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@reminderapp.com")
    
    # SMS (Twilio)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    # WhatsApp
    WHATSAPP_API_KEY: str = os.getenv("WHATSAPP_API_KEY", "")
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "")
    
    # Stripe (Payment Gateway) 
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    @property
    def PAYMENT_SUCCESS_URL(self) -> str:
        return os.getenv("PAYMENT_SUCCESS_URL", 
            "http://localhost:3000/payment/success" if self.IS_DEVELOPMENT else 
            "https://your-production-domain.com/payment/success"
        )
    
    @property
    def PAYMENT_CANCEL_URL(self) -> str:
        return os.getenv("PAYMENT_CANCEL_URL", 
            "http://localhost:3000/payment/cancel" if self.IS_DEVELOPMENT else 
            "https://your-production-domain.com/payment/cancel"
        )

    # Environment
    ENV: str = os.getenv("ENV", "development")  # Options: development, testing, production

    @property
    def IS_DEVELOPMENT(self) -> bool:
        return self.ENV == "development"

    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENV == "production"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:4200").split(",")
    ]
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "True").lower() == "true"
    
    # Scheduler
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    JWT_TOKEN_PREFIX: str = os.getenv("JWT_TOKEN_PREFIX", "Bearer")
    
    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "15"))
    
    # Cookie security
    @property
    def SECURE_COOKIES(self) -> bool:
        """Enable secure cookies based on environment"""
        return os.getenv("SECURE_COOKIES", "False" if self.IS_DEVELOPMENT else "True").lower() == "true"
    
    
    # AWS S3 Storage Configuration
        STORAGE_TYPE: str = Field(default="s3", pattern=r"^(s3|local)$")
    S3_BUCKET_NAME: Optional[str] = Field(
        default=None,
        min_length=3,
        pattern=r"^[a-z0-9.-]{3,63}$",
        examples=["my-production-bucket"]
    )
    S3_ACCESS_KEY: Optional[SecretStr] = Field(default=None, min_length=20)
    S3_SECRET_KEY: Optional[SecretStr] = Field(default=None, min_length=40)
    S3_REGION: Optional[str] = Field(
        default=None,
        pattern=r"^[a-z]{2}-[a-z]+-\d$",
        examples=["us-east-1"]
    )
    S3_OBJECT_ACL: str = Field(default="private", pattern=r"^(private|public-read)$")
    
    # Model configuration
    model_config = ConfigDict(validate_assignment=True, extra="forbid")

    @field_validator("STORAGE_TYPE")
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        if v not in {"s3", "local"}:
            raise ValueError("Storage type must be 's3' or 'local'")
        return v

    @model_validator(mode="after")
    def validate_s3_config(self) -> "Settings":
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
                raise ValueError(
                    f"Missing required S3 configuration for storage type 's3': {', '.join(missing)}"
                )
                
            # Validate bucket name format
            if ".." in self.S3_BUCKET_NAME or self.S3_BUCKET_NAME.startswith("-"):
                raise ValueError("Invalid S3 bucket name format")
        
        return self

    @property
    def s3_credentials_provided(self) -> bool:
        """Check if all S3 credentials are available"""
        return all([
            self.S3_ACCESS_KEY,
            self.S3_SECRET_KEY,
            self.S3_REGION,
            self.S3_BUCKET_NAME
        ])
        
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    DEFAULT_RATE_LIMIT: str = os.getenv("DEFAULT_RATE_LIMIT", "100/minute")

    # Documentation
    DOCS_URL: str = os.getenv("DOCS_URL", "/docs")
    REDOC_URL: str = os.getenv("REDOC_URL", "/redoc")
    OPENAPI_URL: str = os.getenv("OPENAPI_URL", "/openapi.json")

    # Validation
    @property
    def validate_settings(self) -> None:
        """Validate critical settings are properly configured."""
        if self.IS_PRODUCTION:
            # Essential production configurations
            assert self.SECRET_KEY != "your-secret-key-here", "Production SECRET_KEY must be set"
            assert len(self.SECRET_KEY) >= 32, "SECRET_KEY should be at least 32 characters in production"
            
            # Database validation
            assert self.DB_HOST != "localhost", "Production DB_HOST should not be localhost"
            
            # Email validation if needed
            if any([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]):
                assert all([self.SMTP_HOST, self.SMTP_USER, self.SMTP_PASSWORD]), "SMTP settings incomplete"

# Add to Settings class as an inner class
class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"
    case_sensitive = True
    
    def create_settings() -> Settings:
    """Create and validate settings instance."""
    settings_instance = Settings()
    if not settings_instance.IS_DEVELOPMENT:
        settings_instance.validate_settings()
    return settings_instance

settings = create_settings()

settings = Settings()