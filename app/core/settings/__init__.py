# app/core/settings/__init__.py
import os

env = os.getenv("ENV", "development").lower()

if env == "production":
    from .production import ProductionSettings as Settings
elif env == "testing":
    from .testing import TestingSettings as Settings
else:
    from .development import DevelopmentSettings as Settings

settings = Settings()
