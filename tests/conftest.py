import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.core.security import get_password_hash
from app.models.user import User
from app.models.business import Business


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    
    # Create a db session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    # Override the get_db dependency to use the test database
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_user(db_session):
    """Create a test user"""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_superuser=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_superuser(db_session):
    """Create a test superuser"""
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_superuser=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_business(db_session, test_user):
    """Create a test business"""
    business = Business(
        name="Test Business",
        description="A test business",
        email="business@example.com",
        owner_id=test_user.id
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


@pytest.fixture
def token_headers(client, test_user):
    """Get token headers for authentication"""
    login_data = {
        "username": test_user.email,
        "password": "password",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def superuser_token_headers(client, test_superuser):
    """Get token headers for superuser authentication"""
    login_data = {
        "username": test_superuser.email,
        "password": "password",
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}