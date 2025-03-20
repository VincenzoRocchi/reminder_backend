from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.api.routes import api_router
from app.api.endpoints.businesses import router as businesses_router  # <-- Aggiunto
from app.database import engine, Base

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modificare per la produzione - limitare agli origin specifici
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Monta il router principale delle API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Monta il router delle businesses all'interno del router principale
app.include_router(businesses_router, prefix=f"{settings.API_V1_STR}/businesses")

# Create tables in the database
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    """
    Root endpoint to check if the API is running
    """
    return {"message": "Welcome to the Reminder App API!"}
