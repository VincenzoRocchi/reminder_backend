from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import importlib.util
from pathlib import Path

from app import __version__
from app.core.settings import settings
from app.api.routes import api_router
from app.database import engine, Base
from app.core.logging_setup import setup_logging
from app.core.exception_handlers import register_exception_handlers
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware, JSONSanitizerMiddleware
from app.events.monitoring import monitoring_router

# Set up logging first
setup_logging()

# Configure module logger
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Reminder App API for managing reminders, notifications, and sender identities",
    version=__version__,
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

# Add JSON sanitizer middleware (add this before CORS middleware)
app.add_middleware(JSONSanitizerMiddleware)

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
    return {
        "message": "Welcome to the Reminder App API!",
        "version": __version__,
        "docs_url": settings.DOCS_URL
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring systems
    """
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": __version__
    }

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
    
    # Load admin configuration from scripts/admin_setup.py if available
    admin_config = load_admin_config()
    
    db = SessionLocal()
    try:
        # Check if admin superuser already exists
        admin = db.query(User).filter(
            or_(
                User.username == admin_config['username'], 
                User.email == admin_config['email']
            )
        ).first()
        
        if not admin:
            logger.info(f"Creating admin superuser with username: {admin_config['username']}")
            # Create admin user directly in database
            db_obj = User(
                username=admin_config['username'],
                email=admin_config['email'],
                hashed_password=get_password_hash(admin_config['password']),
                first_name=admin_config['first_name'],
                last_name=admin_config['last_name'],
                business_name=admin_config['business_name'],
                phone_number=admin_config['phone_number'],
                is_active=admin_config['is_active'],
                is_superuser=admin_config['is_superuser']
            )
            db.add(db_obj)
            db.commit()
            logger.info("Admin superuser created successfully")
            
            # Write admin credentials to a file for reference if enabled
            if admin_config['create_credentials_file']:
                credentials_file = admin_config['credentials_file_path']
                with open(credentials_file, "w") as f:
                    f.write(f"Admin Username: {admin_config['username']}\n")
                    f.write(f"Admin Email: {admin_config['email']}\n")
                    f.write(f"Admin Password: {admin_config['password']}\n")
                logger.info(f"Admin credentials written to {credentials_file}")
        else:
            logger.info(f"Admin user '{admin_config['username']}' already exists")
    except Exception as e:
        logger.error(f"Error creating admin superuser: {str(e)}")
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

# Helper function to import admin configuration
def load_admin_config():
    """
    Load admin configuration from scripts/admin_setup.py or use defaults.
    
    This function attempts to load the admin_setup.py file from the scripts directory.
    This file should not be committed to version control to protect credentials.
    If the file doesn't exist, default values will be used.
    
    HOW TO USE:
    1. Copy scripts/admin_setup.example.py to scripts/admin_setup.py
    2. Edit scripts/admin_setup.py to set your custom admin credentials
    3. The app will automatically use these credentials when creating the admin user
    
    Default configuration creates an admin with:
    - Username: admin
    - Email: admin@example.com
    - Password: admin (INSECURE! Change this in production)
    
    Returns:
        dict: Admin configuration dictionary
    """
    # Default admin configuration
    default_config = {
        'username': 'admin',
        'email': 'admin@example.com',
        'password': 'admin',
        'first_name': 'Admin',
        'last_name': 'User',
        'business_name': 'Admin Business',
        'phone_number': '+123456789',
        'is_active': True,
        'is_superuser': True,
        'create_credentials_file': True,
        'credentials_file_path': 'admin_credentials.txt'
    }
    
    # Look for admin_setup.py in the scripts directory
    admin_setup_path = Path("scripts/admin_setup.py")
    
    if admin_setup_path.exists():
        try:
            # Load the admin_setup.py module
            spec = importlib.util.spec_from_file_location("admin_setup", admin_setup_path)
            admin_setup = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(admin_setup)
            
            # Get configuration from the module
            config = admin_setup.ADMIN_CONFIG.copy()
            config['create_credentials_file'] = getattr(admin_setup, 'CREATE_CREDENTIALS_FILE', True)
            config['credentials_file_path'] = getattr(admin_setup, 'CREDENTIALS_FILE_PATH', 'admin_credentials.txt')
            
            logger.info("Loaded admin configuration from scripts/admin_setup.py")
            return config
        except Exception as e:
            logger.error(f"Error loading scripts/admin_setup.py: {str(e)}")
            logger.warning("Using default admin configuration")
            return default_config
    else:
        logger.warning(f"scripts/admin_setup.py not found at {admin_setup_path.absolute()}")
        logger.warning("Using default admin configuration (username: 'admin', password: 'admin')")
        logger.warning("For security in production, copy scripts/admin_setup.example.py to scripts/admin_setup.py and modify it")
        return default_config

# Register shutdown event to gracefully stop services
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown services gracefully when application stops"""
    # Import here to avoid circular imports
    from app.services.scheduler_service import scheduler_service
    if hasattr(scheduler_service.scheduler, 'shutdown'):
        scheduler_service.scheduler.shutdown()
        logger.info("Scheduler service shut down")