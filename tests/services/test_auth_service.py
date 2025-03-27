import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from jose import jwt

from app.services.auth_service import AuthService
from app.core.exceptions import TokenExpiredError, TokenInvalidError, UserNotFoundError, InvalidCredentialsError
from app.core.settings import settings


def test_verify_password():
    """Test verifying password against hash"""
    # Test with correct password
    password = "test_password"
    hashed = AuthService.get_password_hash(password)
    
    assert AuthService.verify_password(password, hashed) is True
    
    # Test with incorrect password
    assert AuthService.verify_password("wrong_password", hashed) is False


def test_get_password_hash():
    """Test password hashing"""
    # Test that the same password results in different hashes (salt)
    password = "test_password"
    hash1 = AuthService.get_password_hash(password)
    hash2 = AuthService.get_password_hash(password)
    
    assert hash1 != hash2
    
    # Test that both hashes verify with the original password
    assert AuthService.verify_password(password, hash1) is True
    assert AuthService.verify_password(password, hash2) is True


def test_create_access_token():
    """Test creating an access token"""
    # Create a token with default expiration
    user_id = 123
    token = AuthService.create_access_token(user_id)
    
    # Decode the token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    # Check payload
    assert payload["sub"] == "123"
    assert "exp" in payload
    
    # Check expiration
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Allow 10 seconds tolerance for test execution time
    assert abs((exp - expected_exp).total_seconds()) < 10
    
    # Test with custom expiration
    custom_delta = timedelta(hours=2)
    token = AuthService.create_access_token(user_id, expires_delta=custom_delta)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    exp = datetime.utcfromtimestamp(payload["exp"])
    expected_exp = now + custom_delta
    
    assert abs((exp - expected_exp).total_seconds()) < 10


def test_create_refresh_token():
    """Test creating a refresh token"""
    # Create a refresh token
    user_id = 123
    token = AuthService.create_refresh_token(user_id)
    
    # Decode the token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    # Check payload
    assert payload["sub"] == "123"
    assert payload["type"] == "refresh"
    assert "exp" in payload
    
    # Check expiration
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Allow 10 seconds tolerance for test execution time
    assert abs((exp - expected_exp).total_seconds()) < 10


def test_create_password_reset_token():
    """Test creating a password reset token"""
    # Create a password reset token
    user_id = 123
    token = AuthService.create_password_reset_token(user_id)
    
    # Decode the token
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    # Check payload
    assert payload["sub"] == "123"
    assert payload["type"] == "password_reset"
    assert "exp" in payload
    
    # Check expiration
    exp = datetime.utcfromtimestamp(payload["exp"])
    now = datetime.utcnow()
    expected_exp = now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    
    # Allow 10 seconds tolerance for test execution time
    assert abs((exp - expected_exp).total_seconds()) < 10


def test_verify_token_valid():
    """Test verifying a valid token"""
    # Create a token with long expiration
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token
    token_data = AuthService.verify_token(token)
    
    # Check token data
    assert token_data.sub == "123"
    assert datetime.fromtimestamp(token_data.exp) > datetime.utcnow()


def test_verify_token_expired():
    """Test verifying an expired token"""
    # Create an expired token
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() - timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token and expect an exception
    with pytest.raises(TokenExpiredError) as excinfo:
        AuthService.verify_token(token)
    
    assert "expired" in str(excinfo.value).lower()


def test_verify_token_invalid():
    """Test verifying an invalid token"""
    # Create an invalid token
    token = "invalid.token.format"
    
    # Verify the token and expect an exception
    with pytest.raises(TokenInvalidError) as excinfo:
        AuthService.verify_token(token)
    
    assert "invalid" in str(excinfo.value).lower()


def test_verify_access_token():
    """Test verifying an access token"""
    # Create an access token
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token
    token_data = AuthService.verify_access_token(token)
    
    # Check token data
    assert token_data.sub == "123"


def test_verify_refresh_token():
    """Test verifying a refresh token"""
    # Create a refresh token
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "refresh"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token
    token_data = AuthService.verify_refresh_token(token)
    
    # Check token data
    assert token_data.sub == "123"
    
    # Test with wrong token type
    payload["type"] = "access"
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token and expect an exception
    with pytest.raises(TokenInvalidError) as excinfo:
        AuthService.verify_refresh_token(token)
    
    assert "type" in str(excinfo.value).lower()


def test_verify_password_reset_token():
    """Test verifying a password reset token"""
    # Create a password reset token
    payload = {
        "sub": "123",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "type": "password_reset"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token
    token_data = AuthService.verify_password_reset_token(token)
    
    # Check token data
    assert token_data.sub == "123"
    
    # Test with wrong token type
    payload["type"] = "access"
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Verify the token and expect an exception
    with pytest.raises(TokenInvalidError) as excinfo:
        AuthService.verify_password_reset_token(token)
    
    assert "type" in str(excinfo.value).lower()


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_authenticate_user_success(mock_user):
    """Test authenticating a user with valid credentials"""
    # Create a mock user
    mock_user_instance = MagicMock()
    mock_user_instance.id = 123
    
    # Configure get_by_email to return the mock user
    mock_user.get_by_email = AsyncMock(return_value=mock_user_instance)
    
    # Configure verify_password to return True
    with patch.object(AuthService, 'verify_password', return_value=True):
        # Authenticate with valid credentials
        user = await AuthService.authenticate_user("test@example.com", "correct_password")
        
        # Check that the correct user was returned
        assert user.id == 123
        
        # Check that get_by_email was called with the correct argument
        mock_user.get_by_email.assert_called_once_with("test@example.com")


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_authenticate_user_not_found(mock_user):
    """Test authenticating a user that doesn't exist"""
    # Configure get_by_email to return None
    mock_user.get_by_email = AsyncMock(return_value=None)
    
    # Authenticate with non-existent user
    with pytest.raises(UserNotFoundError) as excinfo:
        await AuthService.authenticate_user("nonexistent@example.com", "password")
    
    # Check exception message
    assert "not found" in str(excinfo.value).lower()
    
    # Check that get_by_email was called with the correct argument
    mock_user.get_by_email.assert_called_once_with("nonexistent@example.com")


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(mock_user):
    """Test authenticating a user with wrong password"""
    # Create a mock user
    mock_user_instance = MagicMock()
    mock_user_instance.id = 123
    
    # Configure get_by_email to return the mock user
    mock_user.get_by_email = AsyncMock(return_value=mock_user_instance)
    
    # Configure verify_password to return False
    with patch.object(AuthService, 'verify_password', return_value=False):
        # Authenticate with wrong password
        with pytest.raises(InvalidCredentialsError) as excinfo:
            await AuthService.authenticate_user("test@example.com", "wrong_password")
        
        # Check exception message
        assert "incorrect password" in str(excinfo.value).lower()


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_refresh_access_token(mock_user):
    """Test refreshing an access token"""
    # Create a mock user
    mock_user_instance = MagicMock()
    mock_user_instance.id = 123
    
    # Configure get_by_id to return the mock user
    mock_user.get_by_id = AsyncMock(return_value=mock_user_instance)
    
    # Mock verify_refresh_token to return a token data with sub = 123
    token_data = MagicMock()
    token_data.sub = "123"
    
    with patch.object(AuthService, 'verify_refresh_token', return_value=token_data):
        # Mock create_access_token to return a predictable value
        with patch.object(AuthService, 'create_access_token', return_value="new_access_token"):
            # Refresh access token
            token = await AuthService.refresh_access_token("refresh_token")
            
            # Check that the correct token was returned
            assert token == "new_access_token"
            
            # Check that get_by_id was called with the correct argument
            mock_user.get_by_id.assert_called_once_with("123")
            
            # Check that create_access_token was called with the correct argument
            AuthService.create_access_token.assert_called_once_with(123)


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_refresh_access_token_user_not_found(mock_user):
    """Test refreshing an access token for a non-existent user"""
    # Configure get_by_id to return None
    mock_user.get_by_id = AsyncMock(return_value=None)
    
    # Mock verify_refresh_token to return a token data with sub = 999
    token_data = MagicMock()
    token_data.sub = "999"
    
    with patch.object(AuthService, 'verify_refresh_token', return_value=token_data):
        # Refresh access token for non-existent user
        with pytest.raises(UserNotFoundError) as excinfo:
            await AuthService.refresh_access_token("refresh_token")
        
        # Check exception message
        assert "not found" in str(excinfo.value).lower()
        
        # Check that get_by_id was called with the correct argument
        mock_user.get_by_id.assert_called_once_with("999")


@patch('app.services.auth_service.User')
@pytest.mark.asyncio
async def test_reset_password(mock_user):
    """Test resetting a password"""
    # Create a mock user
    mock_user_instance = MagicMock()
    mock_user_instance.id = 123
    mock_user_instance.save = AsyncMock()
    
    # Configure get_by_id to return the mock user
    mock_user.get_by_id = AsyncMock(return_value=mock_user_instance)
    
    # Mock verify_password_reset_token to return a token data with sub = 123
    token_data = MagicMock()
    token_data.sub = "123"
    
    with patch.object(AuthService, 'verify_password_reset_token', return_value=token_data):
        # Mock get_password_hash to return a predictable value
        with patch.object(AuthService, 'get_password_hash', return_value="new_hashed_password"):
            # Reset password
            await AuthService.reset_password("reset_token", "new_password")
            
            # Check that get_by_id was called with the correct argument
            mock_user.get_by_id.assert_called_once_with("123")
            
            # Check that get_password_hash was called with the correct argument
            AuthService.get_password_hash.assert_called_once_with("new_password")
            
            # Check that the user's password was updated
            assert mock_user_instance.hashed_password == "new_hashed_password"
            
            # Check that save was called
            mock_user_instance.save.assert_called_once() 