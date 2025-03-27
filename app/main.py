from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging

from app.core.settings import settings
from app.api.routes import api_router
from app.database import engine, Base
from app.core.logging_setup import setup_logging
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Set up logging first
setup_logging()

# Configure module logger
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL
)

# Register exception handlers
register_exception_handlers(app)

# Add production-only security middleware
if settings.ENV == "production":
    # Force HTTPS in production
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Only allow requests from defined hosts in production
    allowed_hosts = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else []
    if allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=allowed_hosts
        )

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Set up CORS middleware with values from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Create tables in the database if using SQLite (testing)
if settings.SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    """
    Root endpoint to check if the API is running
    """
    return {"message": "Welcome to the Reminder App API!"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring systems
    """
    return {"status": "healthy", "environment": settings.ENV}

# Register startup event to initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize services when application starts"""
    logger.info(f"Starting application in {settings.ENV} environment")
    
    # Run security checks
    from app.core.security_checker import check_security_at_startup
    security_results = check_security_at_startup(settings)
    if security_results["total_errors"] > 0 and settings.ENV == "production":
        logger.critical(f"Production environment has {security_results['total_errors']} security issues")
        # In a real-world scenario, you might want to prevent startup in production
        # if critical security issues are found
    
    # Import here to avoid circular imports
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()
    logger.info("Scheduler service started")

# Register shutdown event to gracefully stop services
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown services gracefully when application stops"""
    # Import here to avoid circular imports
    from app.services.scheduler_service import scheduler_service
    if hasattr(scheduler_service.scheduler, 'shutdown'):
        scheduler_service.scheduler.shutdown()
        logger.info("Scheduler service shut down")