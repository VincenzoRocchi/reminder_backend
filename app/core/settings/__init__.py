# app/core/settings/__init__.py
import os
from dotenv import load_dotenv
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Determine environment
ENV = os.getenv("ENV", "development")
logger.debug(f"Settings initialization - Environment: {ENV}")

# Try two possible locations for env files - first in env directory, then in root
env_file = Path(f"env/.env.{ENV}")
root_env_file = Path(f".env.{ENV}")

if env_file.exists():
    logger.debug(f"Loading environment file: {env_file}")
    load_dotenv(str(env_file), override=True)
elif root_env_file.exists():
    logger.debug(f"Loading environment file from root: {root_env_file}")
    load_dotenv(str(root_env_file), override=True)
else:
    # Fallback to default .env in env directory
    default_env = Path("env/.env")
    if default_env.exists():
        logger.debug(f"Environment file not found, falling back to {default_env}")
        load_dotenv(str(default_env))
    else:
        logger.warning(f"No environment file found in env directory or root")

# Log key environment values for debugging (redacting sensitive values)
def log_env_var(name, sensitive=False):
    """Log an environment variable for debugging, redacting sensitive values"""
    value = os.getenv(name, "")
    if sensitive and value:
        # Only show the first and last characters of sensitive values
        if len(value) > 6:
            display_value = f"{value[0:3]}...{value[-3:]}"
        else:
            display_value = "****"
    else:
        display_value = value
    logger.debug(f"{name} from env: {display_value!r}")

# Log critical environment variables for debugging
log_env_var("CORS_ORIGINS")
log_env_var("DB_ENGINE")
log_env_var("SECRET_KEY", sensitive=True)
log_env_var("ENV")

# Import the correct settings class based on environment
if ENV == "development":
    logger.debug("Using DevelopmentSettings")
    from .development import DevelopmentSettings as Settings
elif ENV == "production":
    logger.debug("Using ProductionSettings")
    from .production import ProductionSettings as Settings
elif ENV == "testing":
    logger.debug("Using TestingSettings")
    from .testing import TestingSettings as Settings
else:
    # Default to development if unknown environment
    logger.debug(f"Unknown environment '{ENV}', defaulting to DevelopmentSettings")
    from .development import DevelopmentSettings as Settings

try:
    # Create settings instance
    settings = Settings()
    logger.debug("Settings successfully initialized")
    # Log successful creation of settings instance
    logger.debug(f"SECRET_KEY from settings (first few chars): {settings.SECRET_KEY[:5]}...")
except Exception as e:
    logger.error(f"Error initializing settings: {e}", exc_info=True)
    raise
