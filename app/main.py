from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.settings import settings
from app.api.routes import api_router
from app.api.endpoints.businesses import router as businesses_router
from app.database import engine, Base

# Create custom middleware for security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
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

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

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

# Add security headers middleware for all environments
app.add_middleware(SecurityHeadersMiddleware)

# Set up CORS middleware with values from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Use configured origins instead of wildcard "*"
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # More explicit than "*"
    allow_headers=["Authorization", "Content-Type"],  # More explicit than "*"
)

# Mount the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount the businesses router within the main API
app.include_router(businesses_router, prefix=f"{settings.API_V1_STR}/businesses")

# Create tables in the database
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    """
    Root endpoint to check if the API is running
    """
    return {"message": "Welcome to the Reminder App API!"}