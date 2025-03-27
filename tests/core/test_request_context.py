import pytest
import asyncio
from unittest.mock import patch
from typing import Optional, Dict, Any

from app.core.request_context import (
    get_request_id,
    set_request_id,
    get_user_id,
    set_user_id,
    get_request_path,
    set_request_path,
    get_request_ip,
    set_request_ip,
    get_context_value,
    set_context_value,
    get_all_context,
    clear_context,
    RequestContextFilter
)


def test_request_id_context():
    """Test setting and getting request ID"""
    # Clear context before test
    clear_context()
    
    # Default should be None
    assert get_request_id() is None
    
    # Set a value
    test_id = "test-request-id-123"
    set_request_id(test_id)
    
    # Check that the value was set
    assert get_request_id() == test_id
    
    # Clear context after test
    clear_context()


def test_request_id_auto_generation():
    """Test that request ID is auto-generated when None is passed"""
    # Clear context before test
    clear_context()
    
    # Set with auto-generation
    set_request_id(None)
    
    # Check that a value was generated (not None)
    assert get_request_id() is not None
    assert isinstance(get_request_id(), str)
    assert len(get_request_id()) > 0
    
    # Clear context after test
    clear_context()


def test_user_id_context():
    """Test setting and getting user ID"""
    # Clear context before test
    clear_context()
    
    # Default should be None
    assert get_user_id() is None
    
    # Set a value
    test_id = 123
    set_user_id(test_id)
    
    # Check that the value was set
    assert get_user_id() == test_id
    
    # Clear context after test
    clear_context()


def test_request_path_context():
    """Test setting and getting request path"""
    # Clear context before test
    clear_context()
    
    # Default should be None
    assert get_request_path() is None
    
    # Set a value
    test_path = "/api/users"
    set_request_path(test_path)
    
    # Check that the value was set
    assert get_request_path() == test_path
    
    # Clear context after test
    clear_context()


def test_request_ip_context():
    """Test setting and getting request IP"""
    # Clear context before test
    clear_context()
    
    # Default should be None
    assert get_request_ip() is None
    
    # Set a value
    test_ip = "127.0.0.1"
    set_request_ip(test_ip)
    
    # Check that the value was set
    assert get_request_ip() == test_ip
    
    # Clear context after test
    clear_context()


def test_context_value():
    """Test setting and getting arbitrary context values"""
    # Clear context before test
    clear_context()
    
    # Default should be None
    assert get_context_value("test_key") is None
    
    # Set a value
    set_context_value("test_key", "test_value")
    
    # Check that the value was set
    assert get_context_value("test_key") == "test_value"
    
    # Set another value
    set_context_value("another_key", 123)
    
    # Check that both values are available
    assert get_context_value("test_key") == "test_value"
    assert get_context_value("another_key") == 123
    
    # Clear context after test
    clear_context()


def test_get_all_context():
    """Test retrieving all context values"""
    # Clear context before test
    clear_context()
    
    # Set various values
    test_id = "test-request-id"
    test_user_id = 456
    test_path = "/api/items"
    test_ip = "192.168.1.1"
    test_key = "test_value"
    
    set_request_id(test_id)
    set_user_id(test_user_id)
    set_request_path(test_path)
    set_request_ip(test_ip)
    set_context_value("test_key", test_key)
    
    # Get all context
    context = get_all_context()
    
    # Check that the context contains all expected values
    assert context["request_id"] == test_id
    assert context["user_id"] == test_user_id
    assert context["request_path"] == test_path
    assert context["request_ip"] == test_ip
    assert context["extra_context"]["test_key"] == test_key
    
    # Clear context after test
    clear_context()


def test_clear_context():
    """Test clearing context"""
    # Set values
    set_request_id("test-id")
    set_user_id(789)
    set_context_value("key", "value")
    
    # Verify values are set
    assert get_request_id() == "test-id"
    assert get_user_id() == 789
    assert get_context_value("key") == "value"
    
    # Clear context
    clear_context()
    
    # Verify values are cleared
    assert get_request_id() is None
    assert get_user_id() is None
    assert get_context_value("key") is None


@pytest.mark.asyncio
async def test_context_isolation_in_async_tasks():
    """Test that context variables are isolated between async tasks"""
    # Clear context before test
    clear_context()
    
    async def task1():
        set_request_id("task1-id")
        set_user_id(1)
        await asyncio.sleep(0.1)  # Simulate some async operation
        assert get_request_id() == "task1-id"
        assert get_user_id() == 1
    
    async def task2():
        set_request_id("task2-id")
        set_user_id(2)
        await asyncio.sleep(0.1)  # Simulate some async operation
        assert get_request_id() == "task2-id"
        assert get_user_id() == 2
    
    # Run tasks concurrently
    await asyncio.gather(task1(), task2())
    
    # Clear context after test
    clear_context()


def test_request_context_filter():
    """Test the RequestContextFilter for logging"""
    # Set up context
    set_request_id("filter-test-id")
    set_user_id(999)
    set_request_path("/api/test")
    set_request_ip("10.0.0.1")
    set_context_value("custom_field", "custom_value")
    
    # Create filter
    filter_instance = RequestContextFilter()
    
    # Create a mock log record
    class MockRecord:
        def __init__(self):
            self.args = None
            self.request_id = None
            self.user_id = None
            self.request_path = None
            self.request_ip = None
            self.custom_field = None
    
    record = MockRecord()
    
    # Apply filter
    result = filter_instance.filter(record)
    
    # Verify filter passed and injected context
    assert result is True
    assert record.request_id == "filter-test-id"
    assert record.user_id == 999
    assert record.request_path == "/api/test"
    assert record.request_ip == "10.0.0.1"
    assert record.custom_field == "custom_value"
    
    # Clear context after test
    clear_context() 