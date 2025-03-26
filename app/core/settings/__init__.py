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

# Load appropriate environment file
env_file = f".env.{ENV}"
if Path(env_file).exists():
    logger.debug(f"Loading environment file: {env_file}")
    load_dotenv(env_file)
else:
    # Fallback to default .env
    logger.debug("Environment file not found, falling back to .env")
    load_dotenv()

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
