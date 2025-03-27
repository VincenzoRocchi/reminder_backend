from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handler for application-specific exceptions.
    Returns a standardized error response with status code and error details.
    """
    logger.error(
        f"AppException: {str(exc)}",
        extra={"props": {"path": request.url.path, "error_code": exc.error_code}}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": str(exc),
                "details": exc.details if hasattr(exc, "details") else None
            }
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for validation errors.
    Returns detailed information about validation failures.
    """
    error_details = []
    for error in exc.errors():
        error_details.append({
            "loc": error.get("loc", []),
            "msg": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={"props": {"path": request.url.path, "errors": error_details}}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": error_details
            }
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler for database errors.
    Logs the full exception but returns a generic message to the client.
    """
    logger.error(
        f"Database error: {str(exc)}",
        exc_info=True,
        extra={"props": {"path": request.url.path}}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred",
                "details": None  # Don't expose details in production
            }
        }
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Fallback handler for any uncaught exceptions.
    Logs the full traceback but returns a generic error message to the client.
    """
    logger.error(
        f"Uncaught exception: {str(exc)}",
        exc_info=True,
        extra={"props": {"path": request.url.path}}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": None  # Don't expose details in production
            }
        }
    )

def register_exception_handlers(app):
    """
    Register all exception handlers to the FastAPI app.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 