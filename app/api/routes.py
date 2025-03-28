from fastapi import APIRouter

from app.api.endpoints import (
    emailConfigurations, 
    users, 
    clients, 
    reminders, 
    notifications, 
    auth, 
    senderIdentities,
    monitoring
)
from app.events.monitoring import monitoring_router as events_monitoring_router

# Main API router
api_router = APIRouter()

# Include all endpoint routers with their prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# Removed duplicate inclusion of emailConfigurations.router with prefix "/service-accounts"
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(senderIdentities.router, prefix="/sender-identities", tags=["sender-identities"])
api_router.include_router(emailConfigurations.router, prefix="/email-configurations", tags=["email-configurations"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])

# Include event monitoring router (requires admin access)
api_router.include_router(events_monitoring_router)