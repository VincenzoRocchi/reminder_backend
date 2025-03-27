import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt

from app.core.settings import settings
from app.core.security import create_access_token
from app.core.auth import authenticate_user
from app.core.exceptions import AppException
from app.models.users import User


# Fix for OAuth2PasswordRequestForm which is typically filled from a form
class MockOAuth2PasswordRequestForm:
    def __init__(self, username, password):
        self.username = username
        self.password = password


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database"""
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def auth_headers():
    """Create authorization headers with a valid token"""
    # Create a token for user ID 1
    access_token = create_access_token(
        data={"sub": "1"},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_login_access_token_success(client, test_user, db_session):
    """Test successful login and access token generation"""
    # Make login request
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check token structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token payload
    payload = jwt.decode(
        data["access_token"],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    assert payload["sub"] == str(test_user.id)
    
    # Check token expiration
    exp = datetime.fromtimestamp(payload["exp"])
    assert exp > datetime.utcnow()


def test_login_access_token_invalid_credentials(client, test_user, db_session):
    """Test login with invalid credentials"""
    # Make login request with wrong password
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"}
    )
    
    # Check response
    assert response.status_code == 401
    data = response.json()
    
    # Check error message
    assert "error" in data
    assert "incorrect username or password" in data["error"]["message"].lower()


def test_login_access_token_inactive_user(client, db_session):
    """Test login with inactive user"""
    # Create inactive user
    from app.core.security import get_password_hash
    
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("password"),
        is_active=False
    )
    db_session.add(inactive_user)
    db_session.commit()
    
    # Make login request
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "inactive@example.com", "password": "password"}
    )
    
    # Check response
    assert response.status_code == 401


@patch('app.api.endpoints.auth.jwt.decode')
@patch('app.api.endpoints.auth.token_blacklist.add_token')
def test_logout(mock_add_token, mock_jwt_decode, client, auth_headers):
    """Test logout endpoint"""
    # Configure mock
    mock_jwt_decode.return_value = {"jti": "test-jti", "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()}
    
    # Make logout request with token
    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "successfully logged out" in data["detail"].lower()
    
    # Check that token was added to blacklist
    mock_add_token.assert_called_once()
    assert mock_add_token.call_args[0][0] == "test-jti"


def test_logout_no_token(client):
    """Test logout without token"""
    # Make logout request without token
    response = client.post("/api/v1/auth/logout")
    
    # Check response
    assert response.status_code == 401


@patch('app.api.endpoints.auth.jwt.decode')
def test_refresh_token_success(mock_jwt_decode, client, test_user, db_session):
    """Test successful token refresh"""
    # Configure mock
    mock_jwt_decode.return_value = {
        "sub": str(test_user.id),
        "token_type": "refresh"
    }
    
    # Make refresh request
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "valid.refresh.token"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check token structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify refresh token is returned unchanged
    assert data["refresh_token"] == "valid.refresh.token"


@patch('app.api.endpoints.auth.jwt.decode')
def test_refresh_token_invalid_type(mock_jwt_decode, client):
    """Test refresh with wrong token type"""
    # Configure mock to return wrong token type
    mock_jwt_decode.return_value = {
        "sub": "1",
        "token_type": "access"  # Wrong type
    }
    
    # Make refresh request
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.type.token"}
    )
    
    # Check response
    assert response.status_code == 401
    data = response.json()
    
    # Check error message
    assert "error" in data
    assert "invalid token type" in data["error"]["message"].lower()


@patch('app.api.endpoints.auth.jwt.decode')
def test_refresh_token_user_not_found(mock_jwt_decode, client):
    """Test refresh for non-existent user"""
    # Configure mock
    mock_jwt_decode.return_value = {
        "sub": "999",  # Non-existent user ID
        "token_type": "refresh"
    }
    
    # Make refresh request
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "nonexistent.user.token"}
    )
    
    # Check response
    assert response.status_code == 404
    data = response.json()
    
    # Check error message
    assert "error" in data
    assert "user not found" in data["error"]["message"].lower()


def test_read_users_me(client, test_user, auth_headers):
    """Test reading current user information"""
    # Mock get_current_user dependency to return test_user
    with patch('app.api.endpoints.auth.get_current_user', return_value=test_user):
        # Make request
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        # Check user data
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email


def test_read_users_me_no_token(client):
    """Test reading current user without token"""
    # Make request without token
    response = client.get("/api/v1/auth/me")
    
    # Check response
    assert response.status_code == 401


@patch('app.api.endpoints.auth.jwt.decode')
@patch('app.api.endpoints.auth.token_blacklist.is_blacklisted')
def test_verify_token_valid(mock_is_blacklisted, mock_jwt_decode, client):
    """Test token verification with valid token"""
    # Configure mocks
    mock_jwt_decode.return_value = {"jti": "test-jti", "sub": "123"}
    mock_is_blacklisted.return_value = False
    
    # Make verification request
    response = client.post(
        "/api/v1/auth/verify-token",
        json={"token": "valid.token"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    
    # Check verification result
    assert data["valid"] is True
    assert data["user_id"] == "123"
    
    # Check that blacklist was checked
    mock_is_blacklisted.assert_called_once_with("test-jti")


@patch('app.api.endpoints.auth.jwt.decode')
@patch('app.api.endpoints.auth.token_blacklist.is_blacklisted')
def test_verify_token_blacklisted(mock_is_blacklisted, mock_jwt_decode, client):
    """Test token verification with blacklisted token"""
    # Configure mocks
    mock_jwt_decode.return_value = {"jti": "blacklisted-jti", "sub": "123"}
    mock_is_blacklisted.return_value = True
    
    # Make verification request
    response = client.post(
        "/api/v1/auth/verify-token",
        json={"token": "blacklisted.token"}
    )
    
    # Check response
    assert response.status_code == 401
    data = response.json()
    
    # Check error message
    assert "error" in data
    assert "token has been revoked" in data["error"]["message"].lower()


@patch('app.api.endpoints.auth.jwt.decode')
def test_verify_token_invalid(mock_jwt_decode, client):
    """Test token verification with invalid token"""
    # Configure mock to raise an exception
    mock_jwt_decode.side_effect = Exception("Invalid token")
    
    # Make verification request
    response = client.post(
        "/api/v1/auth/verify-token",
        json={"token": "invalid.token"}
    )
    
    # Check response
    assert response.status_code == 500
    data = response.json()
    
    # Check error message
    assert "error" in data
    assert "error verifying token" in data["error"]["message"].lower() 