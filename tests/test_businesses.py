import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.business import Business
from app.core.security import get_password_hash
from app.core.encryption import encryption_service

# Database SQLite in memoria
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def override_get_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(override_get_db):
    def _get_test_db():
        try:
            yield override_get_db
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(override_get_db):
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_superuser=False
    )
    override_get_db.add(user)
    override_get_db.commit()
    override_get_db.refresh(user)
    return user

@pytest.fixture
def mock_get_current_user(test_user):
    with patch("app.api.dependencies.get_current_user") as mock:
        mock.return_value = test_user
        yield mock

# Test base per il servizio di crittografia
def test_encryption_service():
    test_value = "test_password"
    encrypted = encryption_service.encrypt_string(test_value)
    assert encrypted != test_value
    decrypted = encryption_service.decrypt_string(encrypted)
    assert decrypted == test_value

# Test base per la creazione di un'azienda
def test_create_business(client, mock_get_current_user, test_user):
    business_data = {
        "name": "Azienda Test",
        "email": "test@azienda.it",
        "description": "Test descrizione"
    }
    response = client.post(
        "/api/v1/businesses/",
        json=business_data,
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == business_data["name"]
    assert "id" in data

# Test base per ottenere un'azienda
def test_get_business(client, mock_get_current_user, override_get_db, test_user):
    business = Business(
        name="Azienda Test",
        email="test@test.it",
        owner_id=test_user.id
    )
    override_get_db.add(business)
    override_get_db.commit()
    override_get_db.refresh(business)
    
    response = client.get(
        f"/api/v1/businesses/{business.id}",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == business.name

# Test base per l'aggiornamento di un'azienda
def test_update_business(client, mock_get_current_user, override_get_db, test_user):
    business = Business(
        name="Azienda Test",
        email="test@test.it",
        owner_id=test_user.id
    )
    override_get_db.add(business)
    override_get_db.commit()
    override_get_db.refresh(business)
    
    update_data = {
        "name": "Nome Aggiornato"
    }
    response = client.put(
        f"/api/v1/businesses/{business.id}",
        json=update_data,
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]

# Test base per l'eliminazione di un'azienda
def test_delete_business(client, mock_get_current_user, override_get_db, test_user):
    business = Business(
        name="Azienda Test",
        email="test@test.it",
        owner_id=test_user.id
    )
    override_get_db.add(business)
    override_get_db.commit()
    override_get_db.refresh(business)
    
    response = client.delete(
        f"/api/v1/businesses/{business.id}",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 204
    
    response = client.get(
        f"/api/v1/businesses/{business.id}",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response.status_code == 404