"""
Event system monitoring and observability.

This module provides monitoring capabilities for the event system,
allowing visualization of event processing metrics, error rates,
and other important telemetry.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.dispatcher import event_dispatcher
from app.events.persistence import event_store, StoredEvent
from app.api.deps import get_current_admin_user

logger = logging.getLogger(__name__)

# Create router for monitoring endpoints
monitoring_router = APIRouter(
    prefix="/monitoring/events",
    tags=["monitoring"],
    dependencies=[Depends(get_current_admin_user)]
)

@monitoring_router.get("/metrics")
def get_event_metrics():
    """
    Get event processing metrics.
    
    Returns metrics about event processing, including counts, processing times,
    error rates, and retry statistics.
    """
    return event_dispatcher.get_metrics()

@monitoring_router.get("/types")
def get_event_types():
    """
    Get a list of all event types in the system.
    
    Returns a list of all event types that have subscribers.
    """
    return {
        "event_types": list(event_dispatcher.get_subscribed_event_types())
    }

@monitoring_router.get("/stored")
def get_stored_events(
    db: Session = Depends(get_db),
    event_type: Optional[str] = None,
    processed: Optional[bool] = None,
    has_errors: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get stored events from the event store.
    
    Args:
        db: Database session
        event_type: Optional filter by event type
        processed: Optional filter by processed status
        has_errors: Optional filter for events with errors
        limit: Maximum number of events to return
        offset: Number of events to skip
        
    Returns:
        List of stored events
    """
    query = db.query(StoredEvent)
    
    if event_type:
        query = query.filter(StoredEvent.event_type == event_type)
        
    if processed is not None:
        query = query.filter(StoredEvent.processed == processed)
        
    if has_errors is not None:
        if has_errors:
            query = query.filter(StoredEvent.error.isnot(None))
        else:
            query = query.filter(StoredEvent.error.is_(None))
            
    total = query.count()
    
    events = (query
        .order_by(StoredEvent.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    result = []
    for event in events:
        try:
            payload = json.loads(event.payload) if event.payload else {}
            metadata = json.loads(event.metadata) if event.metadata else {}
        except json.JSONDecodeError:
            payload = {"error": "Invalid JSON"}
            metadata = {"error": "Invalid JSON"}
            
        result.append({
            "id": event.id,
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "processed": event.processed,
            "processing_attempts": event.processing_attempts,
            "error": event.error,
            "payload": payload,
            "metadata": metadata
        })
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "events": result
    }

@monitoring_router.get("/stats")
def get_event_stats(
    db: Session = Depends(get_db),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """
    Get statistics about events in the system.
    
    Args:
        db: Database session
        start_time: Optional start time for the time window
        end_time: Optional end time for the time window
        
    Returns:
        Statistics about events
    """
    if not start_time:
        start_time = datetime.utcnow() - timedelta(days=7)
        
    if not end_time:
        end_time = datetime.utcnow()
        
    query = db.query(StoredEvent).filter(
        StoredEvent.timestamp >= start_time,
        StoredEvent.timestamp <= end_time
    )
    
    total_events = query.count()
    processed_events = query.filter(StoredEvent.processed == True).count()
    unprocessed_events = query.filter(StoredEvent.processed == False).count()
    error_events = query.filter(StoredEvent.error.isnot(None)).count()
    
    # Get event counts by type
    event_types_query = (
        db.query(StoredEvent.event_type, db.func.count(StoredEvent.id))
        .filter(
            StoredEvent.timestamp >= start_time,
            StoredEvent.timestamp <= end_time
        )
        .group_by(StoredEvent.event_type)
    )
    
    event_types = {}
    for event_type, count in event_types_query.all():
        event_types[event_type] = count
    
    return {
        "time_window": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "total_events": total_events,
        "processed_events": processed_events,
        "unprocessed_events": unprocessed_events,
        "error_events": error_events,
        "processing_rate": (processed_events / total_events) if total_events > 0 else 1.0,
        "error_rate": (error_events / total_events) if total_events > 0 else 0.0,
        "events_by_type": event_types
    }

@monitoring_router.post("/recover")
async def recover_events(limit: int = 100):
    """
    Manually trigger recovery of unprocessed events.
    
    Args:
        limit: Maximum number of events to recover
        
    Returns:
        Number of recovered events
    """
    from app.events import recover_unprocessed_events
    
    count = await recover_unprocessed_events(limit=limit)
    
    return {"recovered_events": count}

@monitoring_router.post("/reset-metrics")
def reset_metrics():
    """
    Reset all event metrics.
    
    Returns:
        Confirmation message
    """
    event_dispatcher.reset_metrics()
    
    return {"message": "Event metrics reset successfully"} 