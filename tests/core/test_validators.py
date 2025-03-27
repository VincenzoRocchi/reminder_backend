import pytest
from unittest.mock import patch, MagicMock

from app.core.validators import (
    validate_twilio_token,
    validate_smtp_password,
    flexible_field_validator
)
from app.core.exceptions import InvalidConfigurationError


def test_validate_twilio_token_valid():
    """Test that valid Twilio tokens are accepted"""
    valid_token = "SK12345678901234567890123456789012"  # 32 chars, starts with SK
    result = validate_twilio_token(valid_token)
    assert result == valid_token


def test_validate_twilio_token_invalid_prefix():
    """Test that Twilio tokens not starting with SK are rejected"""
    invalid_token = "AB12345678901234567890123456789012"  # 32 chars, starts with AB
    with pytest.raises(ValueError) as exc_info:
        validate_twilio_token(invalid_token)
    assert "Twilio token must be 32 characters and start with 'SK'" in str(exc_info.value)


def test_validate_twilio_token_invalid_length():
    """Test that Twilio tokens with wrong length are rejected"""
    invalid_token = "SK1234567890"  # Too short, but starts with SK
    with pytest.raises(ValueError) as exc_info:
        validate_twilio_token(invalid_token)
    assert "Twilio token must be 32 characters and start with 'SK'" in str(exc_info.value)


def test_validate_smtp_password_valid():
    """Test that valid SMTP passwords are accepted"""
    valid_password = "password12345"  # More than 8 chars
    result = validate_smtp_password(valid_password)
    assert result == valid_password


def test_validate_smtp_password_invalid():
    """Test that SMTP passwords that are too short are rejected"""
    invalid_password = "pass"  # Less than 8 chars
    with pytest.raises(ValueError) as exc_info:
        validate_smtp_password(invalid_password)
    assert "SMTP password must be at least 8 characters" in str(exc_info.value)


@patch('app.core.validators.settings')
def test_flexible_field_validator_strict_validation(mock_settings):
    """Test that flexible_field_validator correctly applies validation when strict validation is on"""
    # Mock settings to enforce strict validation
    mock_settings.should_validate.return_value = True
    
    # Define a simple validation function that rejects empty strings
    def validate_non_empty(value):
        if value == "":
            raise ValueError("Value cannot be empty")
        return value
    
    # Create a validator for a field named 'test_field'
    validator = flexible_field_validator('test_field')(validate_non_empty)
    
    # Test with valid input
    assert validator(None, "non-empty") == "non-empty"
    
    # Test with invalid input, should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        validator(None, "")
    assert "Value cannot be empty" in str(exc_info.value)


@patch('app.core.validators.settings')
@patch('app.core.validators.logger')
def test_flexible_field_validator_non_strict_validation(mock_logger, mock_settings):
    """Test that flexible_field_validator bypasses validation when strict validation is off"""
    # Mock settings to bypass validation
    mock_settings.should_validate.return_value = False
    
    # Define a simple validation function that rejects empty strings
    def validate_non_empty(value):
        if value == "":
            raise ValueError("Value cannot be empty")
        return value
    
    # Create a validator for a field named 'test_field'
    validator = flexible_field_validator('test_field')(validate_non_empty)
    
    # Even with invalid input, should return the original value when validation is bypassed
    assert validator(None, "") == ""
    
    # Verify that a warning was logged
    mock_logger.warning.assert_called_once()
    assert "Pydantic validation bypassed" in mock_logger.warning.call_args[0][0]


@patch('app.core.validators.settings')
def test_flexible_field_validator_none_value(mock_settings):
    """Test that flexible_field_validator handles None values correctly"""
    # Create a validator that would otherwise reject the input
    def validate_non_empty(value):
        if value == "":
            raise ValueError("Value cannot be empty")
        return value
    
    validator = flexible_field_validator('test_field')(validate_non_empty)
    
    # None values should be returned as None without validation
    assert validator(None, None) is None
    
    # Verify settings.should_validate was not called for None values
    mock_settings.should_validate.assert_not_called()


@patch('app.core.validators.settings')
def test_flexible_field_validator_with_invalid_configuration_error(mock_settings):
    """Test that flexible_field_validator correctly handles InvalidConfigurationError"""
    # Mock settings to enforce strict validation
    mock_settings.should_validate.return_value = True
    
    # Define a validation function that raises InvalidConfigurationError
    def validate_config(value):
        if value == "invalid_config":
            raise InvalidConfigurationError("Invalid configuration value")
        return value
    
    # Create a validator for a field named 'config_field'
    validator = flexible_field_validator('config_field')(validate_config)
    
    # Test with valid input
    assert validator(None, "valid_config") == "valid_config"
    
    # Test with invalid input, should raise InvalidConfigurationError
    with pytest.raises(InvalidConfigurationError) as exc_info:
        validator(None, "invalid_config")
    assert "Invalid configuration value" in str(exc_info.value) 