import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware


@pytest.fixture
def app():
    """Create a FastAPI app for testing"""
    return FastAPI()


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    from starlette.testclient import TestClient
    return TestClient(app)


@pytest.mark.asyncio
@patch('app.core.middleware.set_request_id')
@patch('app.core.middleware.set_user_id')
@patch('app.core.middleware.set_request_path')
@patch('app.core.middleware.set_request_ip')
@patch('app.core.middleware.clear_context')
@patch('app.core.middleware.logger')
async def test_request_context_middleware_sets_context(
    mock_logger, mock_clear_context, mock_set_request_ip, 
    mock_set_request_path, mock_set_user_id, mock_set_request_id
):
    """Test that RequestContextMiddleware sets request context"""
    # Create a middleware instance
    middleware = RequestContextMiddleware(None)
    
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"X-Request-ID": "test-request-id"}
    mock_request.url.path = "/api/test"
    mock_request.client.host = "127.0.0.1"
    mock_request.cookies = {}
    
    # Create a mock call_next function
    mock_response = MagicMock(spec=Response)
    async def mock_call_next(request):
        return mock_response
    
    # Call the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify context was set correctly
    mock_set_request_id.assert_called_once_with("test-request-id")
    mock_set_request_path.assert_called_once_with("/api/test")
    mock_set_request_ip.assert_called_once_with("127.0.0.1")
    
    # User ID not set if not in cookie
    mock_set_user_id.assert_not_called()
    
    # Verify context was cleared
    mock_clear_context.assert_called_once()
    
    # Verify request was logged
    mock_logger.info.assert_called()
    assert "Request" in mock_logger.info.call_args[0][0]
    
    # Verify response was logged
    mock_logger.info.assert_called()
    assert "Response" in mock_logger.info.call_args_list[-1][0][0]
    
    # Verify response was returned
    assert response == mock_response


@pytest.mark.asyncio
@patch('app.core.middleware.set_request_id')
@patch('app.core.middleware.set_user_id')
@patch('app.core.middleware.set_request_path')
@patch('app.core.middleware.clear_context')
async def test_request_context_middleware_with_user_id(
    mock_clear_context, mock_set_request_path, 
    mock_set_user_id, mock_set_request_id
):
    """Test that RequestContextMiddleware sets user ID from cookie"""
    # Create a middleware instance
    middleware = RequestContextMiddleware(None)
    
    # Create a mock request with user ID in cookie
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.url.path = "/api/test"
    mock_request.client.host = "127.0.0.1"
    mock_request.cookies = {"user_id": "123"}
    
    # Create a mock call_next function
    mock_response = MagicMock(spec=Response)
    async def mock_call_next(request):
        return mock_response
    
    # Call the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify user ID was set from cookie
    mock_set_user_id.assert_called_once_with(123)
    
    # Verify response was returned
    assert response == mock_response


@pytest.mark.asyncio
@patch('app.core.middleware.set_request_id')
@patch('app.core.middleware.logger')
async def test_request_context_middleware_auto_request_id(
    mock_logger, mock_set_request_id
):
    """Test that RequestContextMiddleware generates request ID if not in headers"""
    # Create a middleware instance
    middleware = RequestContextMiddleware(None)
    
    # Create a mock request without request ID
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}  # No request ID header
    mock_request.url.path = "/api/test"
    mock_request.client.host = "127.0.0.1"
    mock_request.cookies = {}
    
    # Create a mock call_next function
    mock_response = MagicMock(spec=Response)
    async def mock_call_next(request):
        return mock_response
    
    # Call the middleware
    await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify request ID was set (with None to auto-generate)
    mock_set_request_id.assert_called_once_with(None)


@pytest.mark.asyncio
@patch('app.core.middleware.logger')
async def test_request_context_middleware_logs_exception(mock_logger):
    """Test that RequestContextMiddleware logs exceptions"""
    # Create a middleware instance
    middleware = RequestContextMiddleware(None)
    
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}
    mock_request.url.path = "/api/test"
    mock_request.client.host = "127.0.0.1"
    mock_request.cookies = {}
    
    # Create a mock call_next function that raises an exception
    mock_exception = ValueError("Test exception")
    async def mock_call_next(request):
        raise mock_exception
    
    # Call the middleware and expect exception to be re-raised
    with pytest.raises(ValueError) as exc_info:
        await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify the exception was logged
    mock_logger.exception.assert_called_once()
    assert "Error processing request" in mock_logger.exception.call_args[0][0]
    assert exc_info.value == mock_exception


def test_security_headers_middleware_adds_headers(app, client):
    """Test that SecurityHeadersMiddleware adds security headers to responses"""
    # Add the middleware to the app
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add a test endpoint
    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}
    
    # Make a request to the endpoint
    response = client.get("/test")
    
    # Verify security headers are present
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "X-XSS-Protection" in response.headers
    assert "Content-Security-Policy" in response.headers
    
    # Verify header values
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


@pytest.mark.asyncio
async def test_security_headers_middleware_dispatch():
    """Test the dispatch method of SecurityHeadersMiddleware directly"""
    # Create a middleware instance
    middleware = SecurityHeadersMiddleware(None)
    
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    
    # Create a mock response
    mock_response = MagicMock(spec=Response)
    mock_response.headers = {}
    
    # Create a mock call_next function
    async def mock_call_next(request):
        return mock_response
    
    # Call the middleware
    response = await middleware.dispatch(mock_request, mock_call_next)
    
    # Verify response headers were added
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"] 