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

# Only load environment files from the env directory
env_file = Path(f"env/.env.{ENV}")

if env_file.exists():
    logger.debug(f"Loading environment file: {env_file}")
    load_dotenv(env_file)
else:
    # Fallback to default .env in env directory
    default_env = Path("env/.env")
    if default_env.exists():
        logger.debug(f"Environment file not found, falling back to {default_env}")
        load_dotenv(default_env)
    else:
        logger.warning(f"No environment file found in env directory")

# Log the CORS_ORIGINS value for debugging
cors_value = os.getenv("CORS_ORIGINS", "")
logger.debug(f"CORS_ORIGINS from env: {cors_value!r}")

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
except Exception as e:
    logger.error(f"Error initializing settings: {e}", exc_info=True)
    raise
