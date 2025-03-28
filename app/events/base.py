"""
Base classes for the event system.

This module defines the core event structures and interfaces used throughout
the event-driven architecture.
"""

from datetime import datetime
from typing import Dict, Any, Generic, TypeVar, Optional
from pydantic import BaseModel, Field
import uuid
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class EventMetadata(BaseModel):
    """
    Metadata for all events
    
    Contains information about the event that is not specific to the event type
    but is useful for tracking, debugging, and auditing.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[int] = None
    source: str = "system"
    
    class Config:
        frozen = True

class Event(BaseModel, Generic[T]):
    """
    Base class for all events
    
    All events in the system should inherit from this class and define their
    own payload structure.
    """
    event_type: str
    metadata: EventMetadata = Field(default_factory=EventMetadata)
    payload: T
    
    class Config:
        frozen = True
        
    def __str__(self) -> str:
        """String representation of the event for logging"""
        return f"Event({self.event_type}, id={self.metadata.event_id}, user={self.metadata.user_id})" 