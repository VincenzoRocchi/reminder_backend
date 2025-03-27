import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.token_blacklist import TokenBlacklist, is_token_blacklisted


def test_token_blacklist_singleton():
    """Test that TokenBlacklist is a singleton"""
    blacklist1 = TokenBlacklist()
    blacklist2 = TokenBlacklist()
    
    # Both instances should be the same object
    assert blacklist1 is blacklist2


def test_token_blacklist_add_token():
    """Test adding a token to the blacklist"""
    blacklist = TokenBlacklist()
    
    # Clear the blacklist for testing
    blacklist._tokens = {}
    
    # Add a token
    token_jti = "test-jti-1"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    blacklist.add_token(token_jti, expires_at)
    
    # Check that the token is in the blacklist
    assert token_jti in blacklist._tokens
    assert blacklist._tokens[token_jti] == expires_at


def test_token_blacklist_is_blacklisted():
    """Test checking if a token is blacklisted"""
    blacklist = TokenBlacklist()
    
    # Clear the blacklist for testing
    blacklist._tokens = {}
    
    # Add a token
    token_jti = "test-jti-2"
    expires_at = datetime.utcnow() + timedelta(hours=1)
    blacklist.add_token(token_jti, expires_at)
    
    # Check that the token is blacklisted
    assert blacklist.is_blacklisted(token_jti) is True
    
    # Check that a different token is not blacklisted
    assert blacklist.is_blacklisted("different-jti") is False


def test_token_blacklist_clean_expired():
    """Test cleaning expired tokens from the blacklist"""
    blacklist = TokenBlacklist()
    
    # Clear the blacklist for testing
    blacklist._tokens = {}
    
    # Add an expired token
    expired_jti = "expired-jti"
    expired_time = datetime.utcnow() - timedelta(hours=1)
    blacklist._tokens[expired_jti] = expired_time
    
    # Add a valid token
    valid_jti = "valid-jti"
    valid_time = datetime.utcnow() + timedelta(hours=1)
    blacklist._tokens[valid_jti] = valid_time
    
    # Clean expired tokens
    blacklist._clean_expired()
    
    # Check that the expired token is removed
    assert expired_jti not in blacklist._tokens
    
    # Check that the valid token is still there
    assert valid_jti in blacklist._tokens


@patch('app.core.token_blacklist.jwt')
def test_is_token_blacklisted_valid_token(mock_jwt):
    """Test checking if a valid token is blacklisted"""
    # Create a mock decoded token
    mock_jwt.decode.return_value = {"jti": "test-jti-3"}
    
    # Mock the blacklist
    with patch('app.core.token_blacklist.TokenBlacklist') as mock_blacklist_class:
        # Configure the mock blacklist
        mock_blacklist = MagicMock()
        mock_blacklist.is_blacklisted.return_value = False
        mock_blacklist_class.return_value = mock_blacklist
        
        # Check if the token is blacklisted
        result = is_token_blacklisted("valid-token")
        
        # The token should not be blacklisted
        assert result is False
        
        # Verify the token was decoded
        mock_jwt.decode.assert_called_once()
        
        # Verify the blacklist was checked with the correct JTI
        mock_blacklist.is_blacklisted.assert_called_once_with("test-jti-3")


@patch('app.core.token_blacklist.jwt')
def test_is_token_blacklisted_blacklisted_token(mock_jwt):
    """Test checking if a blacklisted token is blacklisted"""
    # Create a mock decoded token
    mock_jwt.decode.return_value = {"jti": "test-jti-4"}
    
    # Mock the blacklist
    with patch('app.core.token_blacklist.TokenBlacklist') as mock_blacklist_class:
        # Configure the mock blacklist to indicate the token is blacklisted
        mock_blacklist = MagicMock()
        mock_blacklist.is_blacklisted.return_value = True
        mock_blacklist_class.return_value = mock_blacklist
        
        # Check if the token is blacklisted
        result = is_token_blacklisted("blacklisted-token")
        
        # The token should be blacklisted
        assert result is True
        
        # Verify the token was decoded
        mock_jwt.decode.assert_called_once()
        
        # Verify the blacklist was checked with the correct JTI
        mock_blacklist.is_blacklisted.assert_called_once_with("test-jti-4")


@patch('app.core.token_blacklist.jwt')
def test_is_token_blacklisted_invalid_token(mock_jwt):
    """Test checking if an invalid token is blacklisted"""
    # Configure jwt.decode to raise an exception for invalid tokens
    mock_jwt.decode.side_effect = Exception("Invalid token")
    
    # Check if the token is blacklisted
    result = is_token_blacklisted("invalid-token")
    
    # The function should return False for invalid tokens
    assert result is False
    
    # Verify decode was attempted
    mock_jwt.decode.assert_called_once()


def test_token_blacklist_str_representation():
    """Test the string representation of the TokenBlacklist"""
    blacklist = TokenBlacklist()
    
    # Clear the blacklist for testing
    blacklist._tokens = {}
    
    # Add some tokens
    blacklist._tokens["jti-1"] = datetime(2023, 1, 1, 12, 0)
    blacklist._tokens["jti-2"] = datetime(2023, 1, 2, 12, 0)
    
    # Get the string representation
    str_repr = str(blacklist)
    
    # Check that it contains the expected information
    assert "TokenBlacklist" in str_repr
    assert "2 tokens" in str_repr


def test_token_blacklist_repr_representation():
    """Test the repr representation of the TokenBlacklist"""
    blacklist = TokenBlacklist()
    
    # Clear the blacklist for testing
    blacklist._tokens = {}
    
    # Add some tokens
    blacklist._tokens["jti-1"] = datetime(2023, 1, 1, 12, 0)
    
    # Get the repr representation
    repr_str = repr(blacklist)
    
    # Check that it contains the expected information
    assert "TokenBlacklist" in repr_str
    assert "1 tokens" in repr_str 