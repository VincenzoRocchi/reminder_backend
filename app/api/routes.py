from fastapi import APIRouter

from app.api.endpoints import users, service_accounts, clients, reminders, notifications, auth, customers

# Main API router
api_router = APIRouter()

# Include all endpoint routers with their prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(service_accounts.router, prefix="/service-accounts", tags=["service-accounts"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])