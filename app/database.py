from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from app.core.settings.base import BaseAppSettings
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Create declarative base instance
Base = declarative_base()

def get_engine(settings: BaseAppSettings):
    """
    Create SQLAlchemy engine based on settings.
    Handles different database engines (mysql+pymysql, postgresql, sqlite) appropriately.
    """
    if settings.SQLALCHEMY_DATABASE_URI:
        # If URI is explicitly provided, use it
        database_url = settings.SQLALCHEMY_DATABASE_URI
    else:
        if settings.DB_ENGINE == 'sqlite':
            # Special case for SQLite
            database_url = f"sqlite:///{settings.DB_NAME}"
        else:
            # For other databases (mysql+pymysql, postgresql, etc.)
            database_url = f"{settings.DB_ENGINE}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            
            # Add SSL for non-development environments
            if settings.ENV != "development":
                database_url += "?ssl=true"

    # Configure engine based on database type
    if settings.DB_ENGINE == 'sqlite':
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            echo=settings.SQL_ECHO,
            connect_args={"check_same_thread": False}  # Allows SQLite to be used with multiple threads
        )
    else:
        # Configuration for other databases (MySQL, PostgreSQL, etc.)
        engine = create_engine(
            database_url,
            echo=settings.SQL_ECHO,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT
        )
    
    return engine

# Create engine instance
engine = None

def init_db(settings: BaseAppSettings):
    """Initialize database connection"""
    global engine
    engine = get_engine(settings)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    return engine

# SessionLocal class will be used to create database sessions
SessionLocal = None

def init_sessionmaker(engine):
    """Initialize session maker"""
    global SessionLocal
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db() -> Generator:
    """
    Context manager for database sessions.
    Usage:
        with get_db() as db:
            db.query(...)
    """
    if SessionLocal is None:
        raise RuntimeError("Database session factory not initialized. Call init_sessionmaker first.")
        
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def get_db_session():
    """
    Dependency for FastAPI endpoints.
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db_session)):
            ...
    """
    with get_db() as session:
        yield session
