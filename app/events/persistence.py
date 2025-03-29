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
from sqlalchemy.pool import QueuePool

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

def serialize_event(event: Event) -> Dict[str, Any]:
    """
    Serialize an Event object to a dict suitable for storage
    
    Args:
        event: The event to serialize
        
    Returns:
        A dictionary with the event data
        
    Raises:
        EventSerializationError: If the event cannot be serialized
    """
    try:
        # Convert event to dict
        event_dict = event.model_dump()
        
        # Extract and convert metadata
        metadata = event_dict.pop("metadata")
        
        return {
            "payload": event_dict,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Error serializing event: {str(e)}")
        raise EventSerializationError(f"Failed to serialize event: {str(e)}")

def deserialize_event(stored_event: StoredEvent) -> Event:
    """
    Deserialize a StoredEvent to an Event object
    
    Args:
        stored_event: The stored event to deserialize
        
    Returns:
        The deserialized Event
        
    Raises:
        EventDeserializationError: If the event cannot be deserialized
    """
    try:
        # Parse payload and metadata from JSON
        payload = json.loads(stored_event.payload)
        metadata = json.loads(stored_event.event_metadata)
        
        # Reconstruct the event type
        event_type = stored_event.event_type
        
        # Look up the event class based on event_type
        from app.events.types import EVENT_CLASSES
        event_class = EVENT_CLASSES.get(event_type)
        
        if not event_class:
            raise EventDeserializationError(f"Unknown event type: {event_type}")
        
        # Create metadata object
        metadata_obj = EventMetadata(**metadata)
        
        # Create event object with metadata
        payload["metadata"] = metadata_obj
        event = event_class(**payload)
        
        return event
    except Exception as e:
        logger.error(f"Error deserializing event: {str(e)}")
        raise EventDeserializationError(f"Failed to deserialize event: {str(e)}")

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
        # Use provided URL, or settings URL
        self.db_url = db_url or settings.EVENT_STORE_URL
        
        logger.debug(f"Initializing event store with URL: {self.db_url}")
        
        # Configure engine based on database type
        if self.db_url.startswith('sqlite'):
            # SQLite-specific configuration
            self.engine = create_engine(
                self.db_url,
                echo=settings.SQL_ECHO,
                connect_args={"check_same_thread": False}  # Allows SQLite to be used with multiple threads
            )
        else:
            # Configuration for other databases (MySQL, PostgreSQL, etc.)
            self.engine = create_engine(
                self.db_url,
                echo=settings.SQL_ECHO,
                poolclass=QueuePool,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT
            )
        
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
                logger.debug(f"Marked event as processed: {event_id}")
            else:
                logger.warning(f"Event not found for marking as processed: {event_id}")
    
    def get_unprocessed_events(self, limit: int = 100) -> List[StoredEvent]:
        """
        Get unprocessed events from the store.
        
        Args:
            limit: Maximum number of events to retrieve
            
        Returns:
            List of unprocessed events
        """
        with self.SessionLocal() as session:
            events = session.query(StoredEvent).filter(
                StoredEvent.processed == False,
                StoredEvent.processing_attempts < settings.EVENT_MAX_RETRIES
            ).order_by(StoredEvent.timestamp.asc()).limit(limit).all()
            
            logger.debug(f"Retrieved {len(events)} unprocessed events")
            return events
    
    def get_event_by_id(self, event_id: str) -> Optional[StoredEvent]:
        """
        Get an event by ID.
        
        Args:
            event_id: The ID of the event to retrieve
            
        Returns:
            The stored event, or None if not found
        """
        with self.SessionLocal() as session:
            event = session.query(StoredEvent).filter(StoredEvent.event_id == event_id).first()
            return event
    
    def search_events(
        self, 
        event_type: str = None, 
        start_time: datetime = None, 
        end_time: datetime = None,
        processed: bool = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoredEvent]:
        """
        Search for events by various criteria.
        
        Args:
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time
            processed: Filter by processed status
            limit: Maximum number of events to retrieve
            offset: Number of events to skip
            
        Returns:
            List of matching events
        """
        with self.SessionLocal() as session:
            query = session.query(StoredEvent)
            
            # Apply filters
            if event_type:
                query = query.filter(StoredEvent.event_type == event_type)
            if start_time:
                query = query.filter(StoredEvent.timestamp >= start_time)
            if end_time:
                query = query.filter(StoredEvent.timestamp <= end_time)
            if processed is not None:
                query = query.filter(StoredEvent.processed == processed)
                
            # Apply pagination
            query = query.order_by(StoredEvent.timestamp.desc())
            query = query.offset(offset).limit(limit)
            
            return query.all()

# Global instance of event store
event_store = EventStore() 