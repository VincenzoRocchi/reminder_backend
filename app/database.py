from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.settings import settings

# Create SQLAlchemy engine with the database URI from settings
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# Create a session factory for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Create a new database session for each request,
    and close it when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
