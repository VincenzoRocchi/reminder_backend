from fastapi import APIRouter

from app.api.endpoints import users, businesses, reminders, notifications, auth

# Main API router
api_router = APIRouter()

# Include all endpoint routers with their prefixes and tags
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(businesses.router, prefix="/businesses", tags=["businesses"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])