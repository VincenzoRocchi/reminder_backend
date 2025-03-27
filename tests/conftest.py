import os
import sys
import pytest
import logging
import asyncio
from pathlib import Path
from typing import Generator, Dict, Any, List, AsyncGenerator
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add the root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set testing environment
os.environ["ENV"] = "testing"

# Import after setting environment
from app.main import app
from app.database import SessionLocal, Base, engine
from app.core.logging_setup import setup_logging
from app.core.database import Base as CoreBase
from app.core.security.auth import create_access_token
from app.models.users import User
from app.models.clients import Client
from app.models.reminders import Reminder, NotificationTypeEnum
from app.api.deps import get_db


# Initialize logging for tests
setup_logging()


class LogCaptureHandler(logging.Handler):
    """Custom handler to capture log records during tests"""
    
    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []
        
    def emit(self, record):
        self.records.append(record)
        
    def clear(self):
        self.records = []
        
    def get_messages(self) -> List[str]:
        """Get all captured log messages"""
        return [self.format(record) for record in self.records]
    
    def get_records_for_logger(self, logger_name: str) -> List[logging.LogRecord]:
        """Get records for a specific logger"""
        return [r for r in self.records if r.name == logger_name or r.name.startswith(f"{logger_name}.")]


@pytest.fixture(scope="session")
def log_capture() -> LogCaptureHandler:
    """Fixture to capture logs during tests"""
    # Create and configure the handler
    handler = LogCaptureHandler()
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    
    # Add handler to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Store original level to restore later
    original_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)
    
    yield handler
    
    # Teardown: restore original level and remove handler
    root_logger.setLevel(original_level)
    root_logger.removeHandler(handler)


@pytest.fixture(scope="session")
def db_engine():
    """Create the test database engine"""
    # Create test tables
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator:
    """Create a new database session for each test"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client() -> Generator:
    """Return a TestClient for testing the API endpoints"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def reset_log_capture(log_capture):
    """Reset log capture before each test"""
    log_capture.clear()
    yield 


# Configure test database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a clean database session for a test.
    
    This fixture creates tables defined in Base.metadata.
    Use it when you need a database session that is isolated from other tests.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI TestClient that uses the db_session fixture to override
    the get_db dependency that is injected into routes.
    """
    async def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.close = AsyncMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Create a mock User for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.hashed_password = "hashedpassword123"
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


@pytest.fixture
def mock_client():
    """Create a mock Client for testing."""
    client = MagicMock(spec=Client)
    client.id = 1
    client.user_id = 1
    client.name = "Test Client"
    client.email = "client@example.com"
    client.phone_number = "+1234567890"
    client.active = True
    client.created_at = datetime.utcnow()
    client.updated_at = datetime.utcnow()
    return client


@pytest.fixture
def mock_reminder():
    """Create a mock Reminder for testing."""
    reminder = MagicMock(spec=Reminder)
    reminder.id = 1
    reminder.user_id = 1
    reminder.client_id = 1
    reminder.title = "Test Reminder"
    reminder.description = "This is a test reminder"
    reminder.notification_type = NotificationTypeEnum.EMAIL
    reminder.is_recurring = True
    reminder.recurrence_pattern = "daily"
    reminder.next_execution = datetime.utcnow() + timedelta(days=1)
    reminder.active = True
    reminder.created_at = datetime.utcnow()
    reminder.updated_at = datetime.utcnow()
    return reminder


@pytest.fixture
def mock_create_user_data():
    """Create data for creating a user."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Password123!",
        "confirm_password": "Password123!"
    }


@pytest.fixture
def mock_login_data():
    """Create data for user login."""
    return {
        "username": "testuser",
        "password": "Password123!"
    }


@pytest.fixture
def valid_token_headers(mock_user) -> Dict[str, str]:
    """
    Create headers with a valid access token.
    """
    access_token = create_access_token(
        data={"sub": str(mock_user.id), "username": mock_user.username},
        expires_delta=timedelta(minutes=60)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def invalid_token_headers() -> Dict[str, str]:
    """
    Create headers with an invalid access token.
    """
    return {"Authorization": "Bearer invalid_token"}


@pytest.fixture
def test_data():
    """
    Provides a dictionary of test data that can be used throughout tests.
    Modify this fixture to include any test data needed for your tests.
    """
    return {
        "user": {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123!",
        },
        "client": {
            "id": 1,
            "name": "Test Client",
            "email": "client@example.com",
            "phone_number": "+1234567890",
        },
        "reminder": {
            "id": 1,
            "title": "Test Reminder",
            "description": "This is a test reminder",
            "notification_type": NotificationTypeEnum.EMAIL,
            "is_recurring": True,
            "recurrence_pattern": "daily",
        }
    }


@pytest.fixture(scope="function", autouse=True)
def reset_mocks():
    """Reset all mocks after each test function."""
    for m in [m for m in globals().values() if isinstance(m, MagicMock)]:
        m.reset_mock() 