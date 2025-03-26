from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import contextlib
from typing import Generator
import os

from app.core.settings import settings

# Determine if using SQLite (for testing) or another database
is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith('sqlite')

# Connection pool configuration - optimized for different database types
engine_args = {
    "echo": settings.SQL_ECHO,  # SQL query logging based on settings
}

# Add connection pooling options only for non-SQLite databases
if not is_sqlite:
    engine_args.update({
        "pool_pre_ping": True,  # Enable connection health checks
        "pool_recycle": 3600,   # Recycle connections after 1 hour
        "pool_size": 10,        # Default connection pool size
        "max_overflow": 20,     # Allow 20 connections beyond pool_size when needed
        "pool_timeout": 30,     # Wait up to 30 seconds for a connection when pool is full
    })

# Create SQLAlchemy engine with appropriate configuration
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    **engine_args
)

# Create a session factory with optimal settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevents additional DB queries after commit
)

# Create a base class for models
Base = declarative_base()


# Dependency to get DB session with context management
def get_db() -> Generator:
    """
    Create a new database session for each request,
    and close it when the request is done.
    
    Returns:
        Generator yielding the database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context manager for when you need a DB session outside of FastAPI dependencies
@contextlib.contextmanager
def db_session():
    """
    Context manager for database sessions.
    Usage:
        with db_session() as db:
            # Use db session here
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
