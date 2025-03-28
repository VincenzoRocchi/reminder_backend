"""
Monitoring API endpoints.

This module provides endpoints for monitoring the application's health, event system,
and other operational aspects.
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.events.dispatcher import event_dispatcher
from app.core.security import get_current_active_superuser
from app.schemas.user import User

router = APIRouter()

@router.get("/events/metrics", response_model=Dict[str, Any])
async def get_event_system_metrics(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get metrics for the event system.
    
    This endpoint provides information about event processing, including:
    - Number of processed events by type
    - Number of failed events by type
    - Average processing time by event type
    - Error counts by handler
    
    Only superusers can access this endpoint.
    """
    return event_dispatcher.get_metrics()

@router.get("/events/subscriptions", response_model=Dict[str, Any])
async def get_event_subscriptions(
    current_user: User = Depends(get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get information about event subscriptions.
    
    This endpoint provides information about which event types have subscribers
    and how many subscribers they have, both synchronous and asynchronous.
    
    Only superusers can access this endpoint.
    """
    return event_dispatcher.get_subscription_info()

@router.post("/events/reset-metrics", status_code=status.HTTP_204_NO_CONTENT)
async def reset_event_metrics(
    current_user: User = Depends(get_current_active_superuser)
) -> None:
    """
    Reset all event system metrics.
    
    This endpoint resets all metrics tracked by the event system, including:
    - Processed event counts
    - Failed event counts
    - Processing times
    - Error counts
    
    Only superusers can access this endpoint.
    """
    event_dispatcher.reset_metrics()
    return None 