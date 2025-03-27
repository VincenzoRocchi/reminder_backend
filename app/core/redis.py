from typing import Optional
import redis
import logging
import os
from app.core.exceptions import RedisError

logger = logging.getLogger(__name__)

class RedisConnection:
    """
    Manages Redis connections with proper error handling and connection pooling.
    """
    
    _instance: Optional['RedisConnection'] = None
    _redis_client: Optional[redis.Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Import settings here to avoid circular imports
        from app.core.settings import settings
        
        # Skip Redis initialization for non-production environments if not explicitly enabled
        if not settings.USE_REDIS:
            logger.info("Redis disabled in current environment. Using in-memory fallbacks.")
            return
            
        if self._redis_client is None:
            try:
                # Get Redis configuration from settings
                redis_url = settings.REDIS_URL
                redis_password = settings.REDIS_PASSWORD
                
                # Create Redis connection pool
                self._redis_client = redis.from_url(
                    redis_url,
                    password=redis_password,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test connection
                self._redis_client.ping()
                logger.info("Successfully connected to Redis")
                
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                if settings.IS_PRODUCTION:
                    raise RedisError(f"Redis connection failed: {str(e)}")
                else:
                    logger.warning("Running in non-production mode, continuing without Redis")
            except Exception as e:
                logger.error(f"Unexpected error connecting to Redis: {str(e)}")
                if settings.IS_PRODUCTION:
                    raise RedisError(f"Redis initialization failed: {str(e)}")
                else:
                    logger.warning("Running in non-production mode, continuing without Redis")
    
    @property
    def client(self) -> redis.Redis:
        """Get the Redis client instance"""
        if self._redis_client is None:
            from app.core.settings import settings
            if settings.IS_PRODUCTION:
                raise RedisError("Redis client unavailable but required in production mode")
            # Return dummy object for non-production environments
            return DummyRedisClient()
        return self._redis_client

class DummyRedisClient:
    """Dummy Redis client for environments without Redis"""
    def __init__(self):
        self._data = {}
    
    def setex(self, name, time, value):
        self._data[name] = value
        return True
        
    def get(self, name):
        return self._data.get(name)
        
    def ping(self):
        return True

# Create singleton instance - lazy initialization
redis_connection = RedisConnection()

def get_redis_client():
    """Helper function to get Redis client"""
    return redis_connection.client

def close_redis_connection():
    """Close Redis connection"""
    if redis_connection._redis_client:
        try:
            redis_connection._redis_client.close()
            redis_connection._redis_client = None
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")
            raise RedisError(f"Failed to close Redis connection: {str(e)}") 