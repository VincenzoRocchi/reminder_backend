import time
import logging
import uuid
import json
import re
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Dict, Any, Optional
import asyncio

from app.core.settings import settings
from app.core import request_context

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    - Assigns a unique request ID to each request
    - Logs request details when a request is received
    - Logs response status and timing when a response is sent
    - Skips health check endpoints to reduce log noise
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for health check endpoints
        if request.url.path == "/health" or request.url.path == "/":
            return await call_next(request)
        
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timer
        start_time = time.time()
        
        # Add request ID to request state and context
        request.state.request_id = request_id
        request_context.set_request_id(request_id)
        request_context.set_request_path(request.url.path)
        
        client_host = request.client.host if request.client else None
        request_context.set_request_ip(client_host)
        
        # Log the request
        self._log_request(request, request_id)
        
        # Process the request and catch any exceptions
        try:
            response = await call_next(request)
            
            # Log the response
            process_time = time.time() - start_time
            self._log_response(request, response, process_time, request_id)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # Log any unhandled exceptions
            process_time = time.time() - start_time
            logger.error(
                f"Unhandled exception processing request {request_id}",
                exc_info=True,
                extra={
                    "props": {
                        "method": request.method,
                        "process_time_ms": round(process_time * 1000, 2)
                    }
                }
            )
            # Re-raise to be handled by exception handlers
            raise
        finally:
            # Clear the request context
            request_context.clear_context()
    
    def _log_request(self, request: Request, request_id: str):
        """Log request details."""
        # Don't log request bodies in production for security and performance
        should_log_body = settings.ENV != "production" and request.method in ["POST", "PUT", "PATCH"]
        
        client_host = request.client.host if request.client else None
        
        # Build the log context
        context = {
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Add query parameters in development/testing
        if settings.ENV != "production":
            context["query_params"] = str(request.query_params)
        
        logger.info(f"Request started: {request.method} {request.url.path}", extra={"props": context})
    
    def _log_response(self, request: Request, response: Response, process_time: float, request_id: str):
        """Log response details."""
        # Build the log context
        context = {
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error(f"Request failed: {request.method} {request.url.path}", extra={"props": context})
        elif response.status_code >= 400:
            logger.warning(f"Request error: {request.method} {request.url.path}", extra={"props": context})
        else:
            logger.info(f"Request completed: {request.method} {request.url.path}", extra={"props": context})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers to every response
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Only add HSTS header in production to avoid issues during development
        if settings.ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response 

class JSONSanitizerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to sanitize JSON inputs by ensuring property names are properly quoted.
    This fixes client-side JSON formatting errors before they reach FastAPI's validators.
    """
    async def dispatch(self, request: Request, call_next):
        # Only process POST/PUT/PATCH requests with JSON content
        if request.method in ["POST", "PUT", "PATCH"] and \
           request.headers.get("content-type", "").startswith("application/json"):
            # Need to read the body first
            body = await request.body()
            if body:
                try:
                    # Try to decode the body as a string
                    body_str = body.decode('utf-8')
                    
                    # Check if there are unquoted property names (common JSON error)
                    sanitized_body = self._sanitize_json(body_str)
                    
                    if sanitized_body != body_str:
                        logger.warning(f"Sanitized malformed JSON in request to {request.url.path}")
                        
                        # Create a new request with the sanitized body
                        async def receive():
                            return {"type": "http.request", "body": sanitized_body.encode()}
                        
                        # Override the receive method to return our sanitized body
                        request._receive = receive
                except Exception as e:
                    logger.error(f"Error sanitizing JSON: {str(e)}")
        
        # Continue with the request
        return await call_next(request)
    
    def _sanitize_json(self, json_str: str) -> str:
        """
        Sanitize JSON by ensuring property names are properly quoted.
        This fixes the common error: {key: value} -> {"key": value}
        """
        # This regex finds property names that are not enclosed in quotes
        # It matches: word followed by colon, not preceded by quote
        unquoted_prop_pattern = r'(?<!")\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
        
        # Replace with quoted property names
        sanitized = re.sub(unquoted_prop_pattern, r'"\1":', json_str)
        
        # Validate that the result is valid JSON
        try:
            json.loads(sanitized)
            return sanitized
        except json.JSONDecodeError:
            # If still invalid, return original to not make things worse
            return json_str 