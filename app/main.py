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
from app.events.monitoring import monitoring_router

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

# Mount the event monitoring router for admin access
app.include_router(monitoring_router, prefix=settings.API_V1_STR)

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
    
    # Set up event system with event recovery enabled
    from app.events import setup_event_system
    event_system = setup_event_system(recover_events=True, recovery_limit=100)
    logger.info("Event system initialized with recovery enabled")
    
    # Ensure event store tables are created
    from app.events.persistence import event_store
    logger.info("Event persistence tables initialized")
    
    # Run security checks
    from app.core.security_checker import check_security_at_startup
    security_results = check_security_at_startup(settings)
    if security_results["total_errors"] > 0 and settings.ENV == "production":
        logger.critical(f"Production environment has {security_results['total_errors']} security issues")
        # In a real-world scenario, you might want to prevent startup in production
        # if critical security issues are found
        
    # Create default admin superuser if needed
    from app.database import SessionLocal
    from app.models.users import User
    from app.core.security import get_password_hash
    from sqlalchemy import or_
    import os
    
    db = SessionLocal()
    try:
        # Check if admin superuser already exists
        admin = db.query(User).filter(or_(User.username == "admin", User.email == "admin@example.com")).first()
        if not admin:
            logger.info("Creating default admin superuser")
            # Create admin user directly in database
            admin_password = "admin"
            db_obj = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash(admin_password),
                first_name="Admin",
                last_name="User",
                business_name="Admin Business",
                phone_number="+123456789",
                is_active=True,
                is_superuser=True  # Set as superuser
            )
            db.add(db_obj)
            db.commit()
            logger.info("Default admin superuser created successfully")
            
            # Write admin credentials to a file for reference
            credentials_file = "admin_credentials.txt"
            with open(credentials_file, "w") as f:
                f.write(f"Admin Username: admin\n")
                f.write(f"Admin Email: admin@example.com\n")
                f.write(f"Admin Password: {admin_password}\n")
            logger.info(f"Admin credentials written to {credentials_file}")
    except Exception as e:
        logger.error(f"Error creating default admin superuser: {str(e)}")
        db.rollback()
    finally:
        db.close()
    
    # Import here to avoid circular imports
    from app.services.scheduler_service import scheduler_service
    scheduler_started = scheduler_service.start()
    
    if scheduler_started:
        logger.info("Scheduler service is active and processing reminders")
    else:
        logger.info("Scheduler service is disabled for this environment")

# Register shutdown event to gracefully stop services
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown services gracefully when application stops"""
    # Import here to avoid circular imports
    from app.services.scheduler_service import scheduler_service
    if hasattr(scheduler_service.scheduler, 'shutdown'):
        scheduler_service.scheduler.shutdown()
        logger.info("Scheduler service shut down")