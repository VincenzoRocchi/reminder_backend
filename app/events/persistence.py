"""
Event persistence module.

This module provides functionality for persisting events to a durable store,
enabling event sourcing patterns, replay capabilities, and ensuring
delivery guarantees even in case of system failures.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.events.base import Event, EventMetadata
from app.events.exceptions import EventSerializationError, EventDeserializationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

# SQLAlchemy model for stored events
Base = declarative_base()

class StoredEvent(Base):
    """Database model for stored events"""
    __tablename__ = "event_log"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(36), unique=True, index=True)
    event_type = Column(String(255), index=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    payload = Column(Text)
    event_metadata = Column(Text)
    processed = Column(Boolean, default=False, index=True)
    processing_attempts = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<StoredEvent(id={self.id}, event_type={self.event_type}, timestamp={self.timestamp})>"

# Serialization helpers
def serialize_event(event: Event) -> Dict[str, Any]:
    """
    Serialize an event to a JSON-compatible dictionary.
    
    Args:
        event: The event to serialize
        
    Returns:
        Dictionary representation of the event
        
    Raises:
        EventSerializationError: If serialization fails
    """
    try:
        # Use the model's dict method but handle nested models
        return {
            "event_type": event.event_type,
            "metadata": json.loads(event.metadata.json()),
            "payload": json.loads(event.payload.json())
        }
    except Exception as e:
        raise EventSerializationError(
            event_type=event.event_type,
            message=f"Failed to serialize event: {str(e)}"
        )

def deserialize_event(event_data: Dict[str, Any]) -> Event:
    """
    Deserialize an event from a dictionary.
    
    Args:
        event_data: The dictionary representation of the event
        
    Returns:
        The deserialized event
        
    Raises:
        EventDeserializationError: If deserialization fails
    """
    try:
        from app.events.definitions import EVENT_TYPES
        
        event_type = event_data.get("event_type")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown event type: {event_type}")
            
        # Create metadata
        metadata_dict = event_data.get("metadata", {})
        metadata = EventMetadata(**metadata_dict)
        
        # Get payload data
        payload_dict = event_data.get("payload", {})
        
        # For backwards compatibility with older sender_identity events
        if event_type.startswith("sender_identity.") and not payload_dict and "data" in event_data:
            payload_dict = event_data.get("data", {})
        
        # Create the event
        event_class = EVENT_TYPES[event_type]
        
        # Handle both class-based and function-based events
        if event_type.startswith("sender_identity."):
            # For sender identity events, we directly use the Event class
            event = Event(
                event_type=event_type,
                metadata=metadata,
                payload=payload_dict
            )
        else:
            # For other events that use class-based approach
            event = event_class(
                metadata=metadata,
                payload=payload_dict
            )
        
        return event
    except Exception as e:
        raise EventDeserializationError(
            event_type=event_data.get("event_type", "unknown"),
            message=f"Failed to deserialize event: {str(e)}"
        )

class EventStore:
    """
    Persistent storage for events.
    
    This class provides methods for storing and retrieving events from
    a persistent database, ensuring durability and enabling replay.
    """
    
    def __init__(self, db_url: str = None):
        """
        Initialize the event store.
        
        Args:
            db_url: Database connection URL. If not provided, uses the configured event store URL.
        """
        # Use provided URL, or settings URL, or default to SQLite for event store
        self.db_url = db_url or getattr(settings, "EVENT_STORE_URL", None) or "sqlite:///events.db"
        logger.debug(f"Initializing event store with URL: {self.db_url}")
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
        
    def store_event(self, event: Event) -> str:
        """
        Store an event in the persistent store.
        
        Args:
            event: The event to store
            
        Returns:
            The ID of the stored event
            
        Raises:
            EventSerializationError: If the event cannot be serialized
        """
        event_data = serialize_event(event)
        
        with self.SessionLocal() as session:
            stored_event = StoredEvent(
                event_id=event.metadata.event_id,
                event_type=event.event_type,
                timestamp=event.metadata.timestamp,
                payload=json.dumps(event_data["payload"]),
                event_metadata=json.dumps(event_data["metadata"]),
                processed=False
            )
            
            session.add(stored_event)
            session.commit()
            session.refresh(stored_event)
            
            logger.debug(f"Stored event: {event.event_type} (ID: {event.metadata.event_id})")
            return stored_event.event_id
    
    def mark_event_processed(self, event_id: str, error: str = None) -> None:
        """
        Mark an event as processed.
        
        Args:
            event_id: The ID of the event to mark
            error: Optional error message if the event processing failed
        """
        with self.SessionLocal() as session:
            stored_event = session.query(StoredEvent).filter(StoredEvent.event_id == event_id).first()
            
            if stored_event:
                stored_event.processed = True if not error else False
                stored_event.processing_attempts += 1
                stored_event.error = error
                
                session.commit()
    
    def get_unprocessed_events(self, limit: int = 100) -> List[Event]:
        """
        Get unprocessed events from the store.
        
        Args:
            limit: Maximum number of events to retrieve
            
        Returns:
            List of unprocessed events
        """
        result = []
        
        with self.SessionLocal() as session:
            stored_events = (
                session.query(StoredEvent)
                .filter(StoredEvent.processed == False)
                .order_by(StoredEvent.timestamp)
                .limit(limit)
                .all()
            )
            
            for stored_event in stored_events:
                try:
                    event_data = {
                        "event_type": stored_event.event_type,
                        "metadata": json.loads(stored_event.event_metadata),
                        "payload": json.loads(stored_event.payload)
                    }
                    
                    event = deserialize_event(event_data)
                    result.append(event)
                except Exception as e:
                    logger.error(f"Error deserializing event {stored_event.event_id}: {str(e)}")
                    self.mark_event_processed(stored_event.event_id, error=str(e))
            
        return result
    
    def get_events_by_type(self, event_type: str, processed: Optional[bool] = None, limit: int = 100) -> List[Event]:
        """
        Get events by type from the store.
        
        Args:
            event_type: The type of events to retrieve
            processed: Optional filter by processed status
            limit: Maximum number of events to retrieve
            
        Returns:
            List of events of the specified type
        """
        result = []
        
        with self.SessionLocal() as session:
            query = session.query(StoredEvent).filter(StoredEvent.event_type == event_type)
            
            if processed is not None:
                query = query.filter(StoredEvent.processed == processed)
                
            stored_events = query.order_by(StoredEvent.timestamp).limit(limit).all()
            
            for stored_event in stored_events:
                try:
                    event_data = {
                        "event_type": stored_event.event_type,
                        "metadata": json.loads(stored_event.event_metadata),
                        "payload": json.loads(stored_event.payload)
                    }
                    
                    event = deserialize_event(event_data)
                    result.append(event)
                except Exception as e:
                    logger.error(f"Error deserializing event {stored_event.event_id}: {str(e)}")
            
        return result
    
    def replay_events(self, event_types: Optional[List[str]] = None, start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None, limit: int = 1000) -> List[Event]:
        """
        Replay events from the store based on criteria.
        
        Args:
            event_types: Optional list of event types to filter by
            start_time: Optional start time for the replay window
            end_time: Optional end time for the replay window
            limit: Maximum number of events to replay
            
        Returns:
            List of events matching the criteria
        """
        result = []
        
        with self.SessionLocal() as session:
            query = session.query(StoredEvent)
            
            if event_types:
                query = query.filter(StoredEvent.event_type.in_(event_types))
                
            if start_time:
                query = query.filter(StoredEvent.timestamp >= start_time)
                
            if end_time:
                query = query.filter(StoredEvent.timestamp <= end_time)
                
            stored_events = query.order_by(StoredEvent.timestamp).limit(limit).all()
            
            for stored_event in stored_events:
                try:
                    event_data = {
                        "event_type": stored_event.event_type,
                        "metadata": json.loads(stored_event.event_metadata),
                        "payload": json.loads(stored_event.payload)
                    }
                    
                    event = deserialize_event(event_data)
                    result.append(event)
                except Exception as e:
                    logger.error(f"Error deserializing event {stored_event.event_id}: {str(e)}")
            
        return result

# Create a global event store instance
event_store = EventStore() 