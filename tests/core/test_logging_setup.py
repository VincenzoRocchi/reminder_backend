import pytest
import logging
from unittest.mock import patch, MagicMock

from app.core.logging_setup import setup_logging, RequestContextFormatter, log_with_context


def test_request_context_formatter():
    """Test that RequestContextFormatter formats log records correctly"""
    # Create a formatter instance
    formatter = RequestContextFormatter('%(message)s')
    
    # Create a mock record with context attributes
    record = MagicMock()
    record.getMessage.return_value = "Test message"
    record.request_id = "test-request-id"
    record.user_id = 123
    record.request_path = "/api/test"
    record.request_ip = "127.0.0.1"
    record.args = None
    
    # Format the record
    formatted = formatter.format(record)
    
    # Check that the formatted message contains context info
    assert "Test message" in formatted
    assert "test-request-id" in formatted
    assert "123" in formatted  # user_id as string
    assert "/api/test" in formatted
    assert "127.0.0.1" in formatted


def test_request_context_formatter_without_context():
    """Test that RequestContextFormatter works when context attributes are missing"""
    # Create a formatter instance
    formatter = RequestContextFormatter('%(message)s')
    
    # Create a mock record without context attributes
    record = MagicMock()
    record.getMessage.return_value = "Test message"
    record.request_id = None
    record.user_id = None
    record.request_path = None
    record.request_ip = None
    record.args = None
    
    # Format the record
    formatted = formatter.format(record)
    
    # Check that the formatted message doesn't contain context info
    assert "Test message" in formatted
    assert "request_id=None" in formatted or "request_id=" in formatted
    assert "user_id=None" in formatted or "user_id=" in formatted


@patch('app.core.logging_setup.logging.config.dictConfig')
@patch('app.core.logging_setup.settings')
def test_setup_logging_development(mock_settings, mock_dict_config):
    """Test logging setup for development environment"""
    # Configure mock settings for development
    mock_settings.ENV = "development"
    mock_settings.LOG_LEVEL = "DEBUG"
    mock_settings.LOG_FORMAT = "standard"
    mock_settings.LOG_TO_FILE = False
    
    # Call setup_logging
    setup_logging()
    
    # Verify dictConfig was called
    mock_dict_config.assert_called_once()
    
    # Get the config that was passed to dictConfig
    config = mock_dict_config.call_args[0][0]
    
    # Verify config has expected values for development
    assert config["version"] == 1
    assert config["disable_existing_loggers"] is False
    assert config["root"]["level"] == "DEBUG"
    assert len(config["handlers"]) > 0
    assert "console" in config["handlers"]
    assert "file" not in config["handlers"] or not config["handlers"]["file"].get("filename")


@patch('app.core.logging_setup.logging.config.dictConfig')
@patch('app.core.logging_setup.settings')
def test_setup_logging_production(mock_settings, mock_dict_config):
    """Test logging setup for production environment"""
    # Configure mock settings for production
    mock_settings.ENV = "production"
    mock_settings.LOG_LEVEL = "INFO"
    mock_settings.LOG_FORMAT = "json"
    mock_settings.LOG_TO_FILE = True
    mock_settings.LOG_FILE_PATH = "/var/log/app.log"
    
    # Call setup_logging
    setup_logging()
    
    # Verify dictConfig was called
    mock_dict_config.assert_called_once()
    
    # Get the config that was passed to dictConfig
    config = mock_dict_config.call_args[0][0]
    
    # Verify config has expected values for production
    assert config["version"] == 1
    assert config["disable_existing_loggers"] is False
    assert config["root"]["level"] == "INFO"
    assert "json_formatter" in config["formatters"]
    assert "file" in config["handlers"]
    if "file" in config["handlers"]:
        assert config["handlers"]["file"].get("filename") == "/var/log/app.log"


@patch('app.core.logging_setup.logging.config.dictConfig')
@patch('app.core.logging_setup.settings')
def test_setup_logging_testing(mock_settings, mock_dict_config):
    """Test logging setup for testing environment"""
    # Configure mock settings for testing
    mock_settings.ENV = "testing"
    mock_settings.LOG_LEVEL = "DEBUG"
    mock_settings.LOG_FORMAT = "standard"
    mock_settings.LOG_TO_FILE = False
    
    # Call setup_logging
    setup_logging()
    
    # Verify dictConfig was called
    mock_dict_config.assert_called_once()
    
    # Get the config that was passed to dictConfig
    config = mock_dict_config.call_args[0][0]
    
    # Verify config has expected values for testing
    assert config["version"] == 1
    assert config["disable_existing_loggers"] is False
    assert config["root"]["level"] == "DEBUG"
    assert "file" not in config["handlers"] or not config["handlers"]["file"].get("filename")


@patch('app.core.logging_setup.get_all_context')
def test_log_with_context(mock_get_all_context):
    """Test that log_with_context includes context in log records"""
    # Mock the context data
    mock_context = {
        "request_id": "test-req-id",
        "user_id": 456,
        "extra_info": "test value"
    }
    mock_get_all_context.return_value = mock_context
    
    # Create a mock logger
    mock_logger = MagicMock()
    
    # Call log_with_context
    log_with_context(mock_logger, "INFO", "Test message", additional="value")
    
    # Verify logger.log was called with expected arguments
    mock_logger.log.assert_called_once()
    args, kwargs = mock_logger.log.call_args
    
    # First argument should be log level
    assert args[0] == logging.INFO
    
    # Second argument should be message
    assert args[1] == "Test message"
    
    # Context should be included in kwargs
    assert kwargs["request_id"] == "test-req-id"
    assert kwargs["user_id"] == 456
    assert kwargs["additional"] == "value"


@patch('app.core.logging_setup.get_all_context')
def test_log_with_context_explicit_context(mock_get_all_context):
    """Test that log_with_context allows explicit context to override defaults"""
    # Mock the default context data
    mock_default_context = {
        "request_id": "default-req-id",
        "user_id": 456
    }
    mock_get_all_context.return_value = mock_default_context
    
    # Create a mock logger
    mock_logger = MagicMock()
    
    # Call log_with_context with explicit context
    explicit_context = {
        "request_id": "explicit-req-id",
        "custom_field": "custom value"
    }
    log_with_context(mock_logger, "ERROR", "Test with explicit", context=explicit_context)
    
    # Verify logger.log was called with expected arguments
    mock_logger.log.assert_called_once()
    args, kwargs = mock_logger.log.call_args
    
    # First argument should be log level
    assert args[0] == logging.ERROR
    
    # Context should use explicit values where provided
    assert kwargs["request_id"] == "explicit-req-id"  # From explicit context
    assert kwargs["user_id"] == 456  # From default context
    assert kwargs["custom_field"] == "custom value"  # From explicit context 