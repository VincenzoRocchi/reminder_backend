from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import your app models - avoid circular imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import models directly without importing app.main
from app.database import Base
from app.models.users import User
from app.models.emailConfigurations import EmailConfiguration
from app.models.clients import Client
from app.models.reminders import Reminder, ReminderTypeEnum, NotificationTypeEnum
from app.models.reminderRecipient import ReminderRecipient
from app.models.notifications import Notification, NotificationStatusEnum
from app.models.senderIdentities import SenderIdentity

# Import settings directly
from app.core.settings.base import BaseAppSettings
from app.core.settings.development import DevelopmentSettings
from app.core.settings.production import ProductionSettings
from app.core.settings.testing import TestingSettings

# Load environment variables and settings
import os
from dotenv import load_dotenv

# Determine environment
env = os.environ.get("ENV", "development")
# Load appropriate .env file
if env == "development":
    load_dotenv(".env.development")
    settings = DevelopmentSettings()
elif env == "production":
    load_dotenv(".env.production")
    settings = ProductionSettings()
else:  # testing
    load_dotenv(".env.testing")
    settings = TestingSettings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the sqlalchemy.url from the settings
# This is where we fix the placeholder_url issue
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Added for better column type comparison
        compare_server_default=True,  # Added for server default comparison
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use pooled engine for migrations (more efficient than NullPool)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.QueuePool,  # Changed from NullPool for better performance
        pool_size=5,  # Reasonable connection pool size
        max_overflow=10,  # Allow extra connections during spikes
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # Added for better column type comparison
            compare_server_default=True,  # Added for server default comparison
            include_schemas=True,  # Include schema support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()